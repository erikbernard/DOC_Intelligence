"""Document management, inspection, pessimistic locking, and human review endpoints."""

from datetime import datetime, timezone
import copy
import io
from typing import List, Optional
import uuid
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import get_current_user, get_async_db
from app.core.config import settings
from app.core.file_security import FileSecurityError, inspect_file_in_memory
from app.core.logging import app_logger
from app.models.document import Document, DocumentStatus, UploadOrigin
from app.models.persona import Persona
from app.models.template import Template
from app.models.user import User, UserRole
from app.schemas.document import (
    DocumentDetailRead,
    DocumentLockResponse,
    DocumentRead,
    DocumentRejectRequest,
    DocumentReviewUpdate,
)
from app.services.audit_service import record_audit_log
from app.services.lock_service import lock_service
from app.services.persona_service import check_and_update_persona_completion
from app.services.sse_service import publish_event
from app.services.storage.minio_service import minio_service
from app.services.storage.path_formatter import format_storage_path
from app.workers.tasks.ocr_tasks import process_document_ocr
from app.workers.tasks.webhook_tasks import dispatch_workspace_webhooks

router = APIRouter()


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
async def upload_document_internal(
    request: Request,
    persona_id: str = Form(...),
    template_id: Optional[str] = Form(None),
    document_type: str = Form(default="CIN"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Direct internal document upload by authenticated System Operator."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona não encontrada com o ID informado.",
        )

    # 1. Inspect in memory
    file_bytes = await file.read()
    try:
        detected_mime, clean_name = inspect_file_in_memory(
            file_bytes=file_bytes, original_filename=file.filename or "upload"
        )
    except FileSecurityError as sec_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A inspeção de segurança rejeitou o arquivo: {str(sec_err)}",
        )

    # 2. Format path & upload to MinIO
    doc_id = str(uuid.uuid4())
    storage_path = format_storage_path(
        persona_id=persona_id,
        doc_type=document_type,
        doc_id=doc_id,
        sanitized_filename=clean_name,
        file_bytes=file_bytes,
    )
    minio_service.upload_bytes(storage_path, file_bytes, detected_mime)

    # 3. Save record
    doc = Document(
        id=doc_id,
        persona_id=persona_id,
        template_id=template_id,
        raw_file_name=file.filename or "upload",
        sanitized_file_name=clean_name,
        storage_path=storage_path,
        mime_type=detected_mime,
        file_size_bytes=len(file_bytes),
        status=DocumentStatus.PENDING,
        upload_origin=UploadOrigin.SYSTEM_USER,
        created_by_user_id=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # 4. Enqueue OCR Task
    process_document_ocr.delay(doc.id)

    return doc


@router.get("/", response_model=List[DocumentRead])
async def list_documents(
    persona_id: Optional[str] = Query(None),
    template_id: Optional[str] = Query(None),
    status_filter: Optional[DocumentStatus] = Query(None),
    in_review: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """List documents with extensive filtering for conference queue and reports."""
    stmt = select(Document)
    if persona_id:
        stmt = stmt.where(Document.persona_id == persona_id)
    if template_id:
        stmt = stmt.where(Document.template_id == template_id)
    if status_filter:
        stmt = stmt.where(Document.status == status_filter)
    if in_review is True:
        stmt = stmt.where(Document.locked_by_user_id.is_not(None))
    elif in_review is False:
        stmt = stmt.where(Document.locked_by_user_id.is_(None))

    stmt = stmt.order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    docs = result.scalars().all()

    response_docs = []
    for doc in docs:
        item = DocumentRead.model_validate(doc)
        item.preview_url = minio_service.generate_presigned_get_url(doc.storage_path)
        response_docs.append(item)
    return response_docs


@router.get("/{document_id}", response_model=DocumentDetailRead)
async def get_document_detail(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get full document details, OCR results, and secure preview link."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado com o ID informado."
        )

    # Generate secure presigned URL for preview
    preview_url = minio_service.generate_presigned_get_url(doc.storage_path, expires_seconds=1800)

    detail = DocumentDetailRead.model_validate(doc)
    detail.preview_url = preview_url
    return detail


@router.get("/{document_id}/file")
async def stream_document_file(
    document_id: str,
    request: Request,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    """Stream raw document file bytes to authenticated user for side-by-side comparison.
    Supports Authorization Bearer header or ?token=<jwt> query parameter for inline browser viewing.
    """
    from app.core.security import decode_token

    # Authenticate via Header or Query token
    auth_header = request.headers.get("Authorization", "")
    jwt_str = None
    if auth_header.startswith("Bearer "):
        jwt_str = auth_header.split(" ", 1)[1].strip()
    elif token:
        jwt_str = token

    if not jwt_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido.",
        )

    payload = decode_token(jwt_str)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido ou expirado.",
        )

    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado com o ID informado."
        )

    try:
        file_bytes = minio_service.get_bytes(doc.storage_path)
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=doc.mime_type,
            headers={
                "Content-Disposition": f'inline; filename="{doc.sanitized_file_name}"'
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao transmitir o arquivo do documento: {str(exc)}",
        )


@router.post("/{document_id}/lock", response_model=DocumentLockResponse)
async def acquire_document_lock(
    document_id: str,
    session_id: Optional[str] = Query(""),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Acquire pessimistic review lock on a document with 10-minute TTL (RN-07, RN-08)."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado com o ID informado."
        )

    acquired, lock_info = lock_service.acquire_lock(
        doc_id=doc.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        session_id=session_id or "",
        ttl_seconds=settings.LOCK_TTL_SECONDS,
    )

    if not acquired:
        holder_name = lock_info.get("user_name", "outro usuário") if lock_info else "outro usuário"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Este documento já está em edição pelo usuário [{holder_name}] (RN-07).",
        )

    # Update DB lock fields
    doc.locked_by_user_id = current_user.id
    doc.locked_by_user_name = current_user.full_name
    doc.locked_at = datetime.now(timezone.utc)
    await db.commit()

    return DocumentLockResponse(
        document_id=doc.id,
        locked=True,
        locked_by_user_id=current_user.id,
        locked_by_user_name=current_user.full_name,
        locked_at=doc.locked_at,
        message="Lock de conferência adquirido com sucesso por 10 minutos (RN-08).",
    )


@router.post("/{document_id}/unlock")
async def release_document_lock(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Release pessimistic review lock."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado com o ID informado."
        )

    is_admin = current_user.role == UserRole.ADMIN
    lock_service.release_lock(doc.id, current_user.id, is_admin=is_admin)

    doc.locked_by_user_id = None
    doc.locked_by_user_name = None
    doc.locked_at = None
    await db.commit()

    return {"message": "Lock de conferência liberado com sucesso."}


@router.put("/{document_id}/review", response_model=DocumentDetailRead)
async def submit_document_review(
    document_id: str,
    data: DocumentReviewUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Approve / submit human review for a document (RN-10: marks READY, records approved_by)."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )

    # Check imutability: if already READY and user is not admin, block edit
    if doc.status == DocumentStatus.READY and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Documento já aprovado e imutável. Alterações exigem perfil Administrador (RN-10).",
        )

    # Template update if operator specified a different template (e.g. OCR misidentified CIN as RG_ANTIGO)
    target_template_code = data.template_code or data.document_type
    target_template_id = data.template_id

    target_template = None
    if target_template_code or target_template_id:
        conditions = []
        if target_template_code:
            conditions.append(Template.code == target_template_code.upper())
            conditions.append(Template.document_type == target_template_code.upper())
        if target_template_id:
            conditions.append(Template.id == target_template_id)

        stmt = select(Template).where(or_(*conditions))
        target_template = (await db.execute(stmt)).scalars().first()

        if target_template:
            doc.template_id = target_template.id

    # Deepcopy extracted_data to guarantee SQLAlchemy tracks modifications on JSON columns
    current_extracted = copy.deepcopy(doc.extracted_data or {})
    fields = dict(current_extracted.get("fields", {}))

    if target_template:
        current_extracted["document_type"] = target_template.document_type
        current_extracted["template_code"] = target_template.code
    elif target_template_code:
        current_extracted["document_type"] = target_template_code.upper()

    # Merge corrected fields into extracted_data
    for field_key, corrected_val in data.corrected_data.items():
        if field_key in fields:
            fields[field_key]["value"] = corrected_val
            fields[field_key]["is_valid"] = True
            fields[field_key]["confidence"] = 1.0
            fields[field_key]["warning"] = None
        else:
            fields[field_key] = {
                "value": corrected_val,
                "raw_value": str(corrected_val) if corrected_val is not None else None,
                "confidence": 1.0,
                "is_valid": True,
                "is_fuzzy_corrected": False,
                "warning": None,
            }

    # If the operator altered template (e.g. from RG_ANTIGO to CIN),
    # prune obsolete null fields that do not belong to the target template and were not submitted
    if target_template and target_template.fields_schema:
        valid_template_fields = {f.get("name") for f in target_template.fields_schema}
        for f_name in list(fields.keys()):
            if (
                f_name not in valid_template_fields
                and f_name not in data.corrected_data
                and fields[f_name].get("value") is None
            ):
                fields.pop(f_name, None)

    current_extracted["fields"] = fields
    current_extracted["is_auto_approved"] = False
    current_extracted["is_manually_approved"] = True
    current_extracted["manual_review_notes"] = data.notes

    # Clear pending validation errors upon manual human approval (RN-10)
    current_extracted["validation_errors"] = []

    doc.extracted_data = current_extracted
    flag_modified(doc, "extracted_data")

    doc.confidence_score = 1.0  # Human review establishes 100% verified confidence
    doc.status = DocumentStatus.READY
    doc.approved_by_user_id = current_user.id
    doc.approved_at = datetime.now(timezone.utc)
    doc.locked_by_user_id = None
    doc.locked_by_user_name = None
    doc.locked_at = None

    await db.commit()
    await db.refresh(doc)

    # Release Redis lock
    lock_service.release_lock(doc.id, current_user.id, is_admin=True)

    # Record Audit Log
    await record_audit_log(
        db=db,
        action="DOCUMENT_APPROVED_MANUAL",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        user_id=current_user.id,
        details={"notes": data.notes, "corrected_fields": list(data.corrected_data.keys())},
    )

    # Check Persona completion (RN-15)
    await check_and_update_persona_completion(db, doc.persona_id)

    # Publish SSE & Webhooks
    event_payload = {
        "document_id": doc.id,
        "persona_id": doc.persona_id,
        "status": "READY",
        "approved_by": current_user.full_name,
    }
    publish_event("document.ready", event_payload, persona_id=doc.persona_id)
    dispatch_workspace_webhooks.delay(
        event_name="document.ready",
        payload=event_payload,
        document_id=doc.id,
        persona_id=doc.persona_id,
    )

    detail = DocumentDetailRead.model_validate(doc)
    detail.preview_url = minio_service.generate_presigned_get_url(doc.storage_path)
    return detail


@router.post("/{document_id}/reject", response_model=DocumentDetailRead)
async def reject_document_quality(
    document_id: str,
    data: DocumentRejectRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Reject blurry / unreadable document and trigger customer re-upload event (RN-09)."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado com o ID informado."
        )

    doc.status = DocumentStatus.REJECTED
    doc.rejection_reason = data.rejection_reason
    doc.locked_by_user_id = None
    doc.locked_by_user_name = None
    doc.locked_at = None

    await db.commit()
    await db.refresh(doc)

    # Release Redis lock
    lock_service.release_lock(doc.id, current_user.id, is_admin=True)

    # Record Audit Log
    await record_audit_log(
        db=db,
        action="DOCUMENT_REJECTED_QUALITY",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        user_id=current_user.id,
        details={"rejection_reason": data.rejection_reason},
    )

    # Publish SSE and Webhooks to alert external customer/systems (RN-09)
    event_payload = {
        "document_id": doc.id,
        "persona_id": doc.persona_id,
        "status": "REJECTED",
        "rejection_reason": data.rejection_reason,
        "action_required": "RESUBMIT_CLEAR_IMAGE",
    }
    publish_event("document.rejected", event_payload, persona_id=doc.persona_id)
    dispatch_workspace_webhooks.delay(
        event_name="document.rejected",
        payload=event_payload,
        document_id=doc.id,
        persona_id=doc.persona_id,
    )

    detail = DocumentDetailRead.model_validate(doc)
    detail.preview_url = minio_service.generate_presigned_get_url(doc.storage_path)
    return detail
