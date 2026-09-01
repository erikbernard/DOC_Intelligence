"""Public Document Upload endpoint for end-users accessing via signed collection link (RN-11)."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, validate_public_collection_token
from app.core.file_security import FileSecurityError, inspect_file_in_memory
from app.core.logging import app_logger
from app.models.collection_link import CollectionLink
from app.models.document import Document, DocumentStatus, UploadOrigin
from app.schemas.collection_link import PublicUploadResponse
from app.services.sse_service import publish_event
from app.services.storage.minio_service import minio_service
from app.services.storage.path_formatter import format_storage_path
from app.workers.tasks.ocr_tasks import process_document_ocr

router = APIRouter()


@router.post("/upload", response_model=PublicUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def public_upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(default="CIN"),
    template_id: Optional[str] = Form(None),
    token_payload: dict = Depends(validate_public_collection_token),
    db: AsyncSession = Depends(get_async_db),
):
    """Receive document from public applicant link, inspect in memory, save to MinIO, and enqueue OCR."""
    persona_id = token_payload["persona_id"]
    operator_id = token_payload.get("created_by_user_id")
    link_id = token_payload.get("collection_link_id")

    # Verify link usage count
    link = await db.get(CollectionLink, link_id) if link_id else None
    if link:
        if not link.is_active or link.uses_count >= link.max_uses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este link de coleta já atingiu o limite máximo de envios permitidos.",
            )
        link.uses_count += 1
        await db.commit()

    # 1. Read file into memory and perform Multilayer Security Inspection
    file_bytes = await file.read()
    try:
        detected_mime, clean_name = inspect_file_in_memory(
            file_bytes=file_bytes, original_filename=file.filename or "upload"
        )
    except FileSecurityError as sec_err:
        app_logger.warning(f"File security rejection on public upload: {str(sec_err)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A inspeção de segurança rejeitou o arquivo: {str(sec_err)}",
        )

    # 2. Format custom storage path
    doc_id = str(uuid.uuid4())
    storage_path = format_storage_path(
        persona_id=persona_id,
        doc_type=document_type,
        doc_id=doc_id,
        sanitized_filename=clean_name,
        file_bytes=file_bytes,
    )

    # 3. Upload raw file to MinIO S3
    minio_service.upload_bytes(
        storage_path=storage_path,
        data_bytes=file_bytes,
        content_type=detected_mime,
    )

    # 4. Create Document Record in DB
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    document = Document(
        id=doc_id,
        persona_id=persona_id,
        template_id=template_id,
        raw_file_name=file.filename or "upload",
        sanitized_file_name=clean_name,
        storage_path=storage_path,
        mime_type=detected_mime,
        file_size_bytes=len(file_bytes),
        status=DocumentStatus.PENDING,
        upload_origin=UploadOrigin.PUBLIC_LINK,
        created_by_user_id=operator_id,
        collection_link_id=link_id,
        upload_ip_address=client_ip,
        upload_user_agent=user_agent,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # 5. Publish SSE event
    publish_event(
        event_type="document.uploaded",
        payload={
            "document_id": document.id,
            "persona_id": document.persona_id,
            "filename": document.sanitized_file_name,
            "status": document.status.value,
        },
        persona_id=persona_id,
    )

    # 6. Enqueue Celery Async OCR Task
    process_document_ocr.delay(document.id)

    return PublicUploadResponse(
        document_id=document.id,
        status=document.status.value,
        message="Documento recebido com sucesso e enviado para extração automática de OCR.",
        persona_id=persona_id,
    )
