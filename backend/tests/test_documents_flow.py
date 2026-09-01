"""Comprehensive test suite for Document locking, review, rejection, and public upload flow."""

import io
from unittest.mock import MagicMock
import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_collection_link_token
from app.models.collection_link import CollectionLink
from app.models.document import Document, DocumentStatus, UploadOrigin
from app.models.persona import Persona
from app.models.user import User
from app.services.lock_service import lock_service
from app.services.storage.minio_service import minio_service


def create_test_image_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (300, 300), color=(100, 150, 200))
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_document_lock_and_concurrency_conflict(
    client: AsyncClient,
    admin_token: str,
    operator_token: str,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test locking a document for review and blocking concurrent review (RN-07)."""
    # Mock Redis lock
    fake_redis = {}
    mock_r = MagicMock()
    mock_r.set.side_effect = lambda k, v, nx=False, ex=None: (
        fake_redis.setdefault(k, v) == v if nx else bool(fake_redis.update({k: v}) or True)
    )
    mock_r.get.side_effect = lambda k: fake_redis.get(k)
    mock_r.delete.side_effect = lambda k: fake_redis.pop(k, None) is not None
    monkeypatch.setattr(lock_service, "redis_client", mock_r)

    persona = Persona(name="Persona Lock")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    doc = Document(
        persona_id=persona.id,
        raw_file_name="cin.png",
        sanitized_file_name="cin.png",
        storage_path="path/to/cin.png",
        mime_type="image/png",
        file_size_bytes=1200,
        status=DocumentStatus.NEEDS_REVIEW,
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # 1. Admin acquires lock
    resp1 = await client.post(
        f"/api/v1/documents/{doc.id}/lock",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["locked"] is True

    # 2. Operator tries to lock same doc -> 409 Conflict (RN-07)
    resp2 = await client.post(
        f"/api/v1/documents/{doc.id}/lock",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp2.status_code == 409
    assert "já está em edição" in resp2.json()["detail"]

    # 3. Admin unlocks
    unlock_resp = await client.post(
        f"/api/v1/documents/{doc.id}/unlock",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert unlock_resp.status_code == 200


@pytest.mark.asyncio
async def test_document_manual_review_approval(
    client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test manual human review PUT endpoint approving document (RN-10)."""
    monkeypatch.setattr(minio_service, "generate_presigned_get_url", lambda path, **kw: "http://mock-s3/preview")
    from app.workers.tasks.webhook_tasks import dispatch_workspace_webhooks
    monkeypatch.setattr(dispatch_workspace_webhooks, "delay", lambda *a, **k: None)

    persona = Persona(name="Persona Rev")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    doc = Document(
        persona_id=persona.id,
        raw_file_name="cin.png",
        sanitized_file_name="cin.png",
        storage_path="path/to/cin.png",
        mime_type="image/png",
        file_size_bytes=1200,
        status=DocumentStatus.NEEDS_REVIEW,
        extracted_data={"fields": {"cpf": {"value": "000.000.000-00", "is_valid": False}}},
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    review_payload = {
        "corrected_data": {
            "cpf": "111.444.777-35",
            "nome_completo": "MARCOS SILVA CORRIGIDO",
            "data_nascimento": "01/01/1990",
        },
        "notes": "Corrigido pelo operador após conferência visual lado a lado.",
    }

    resp = await client.put(
        f"/api/v1/documents/{doc.id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "READY"
    assert data["extracted_data"]["fields"]["cpf"]["value"] == "111.444.777-35"
    assert data["extracted_data"]["fields"]["cpf"]["confidence"] == 1.0
    assert data["extracted_data"]["validation_errors"] == []
    assert data["confidence_score"] == 1.0
    assert data["approved_by_user_id"] is not None


@pytest.mark.asyncio
async def test_document_manual_review_template_switch(
    client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test operator altering template type during manual review (e.g. from RG_ANTIGO to CIN)."""
    monkeypatch.setattr(minio_service, "generate_presigned_get_url", lambda path, **kw: "http://mock-s3/preview")
    from app.workers.tasks.webhook_tasks import dispatch_workspace_webhooks
    monkeypatch.setattr(dispatch_workspace_webhooks, "delay", lambda *a, **k: None)

    persona = Persona(name="Persona Template Switch", required_document_types=["CIN"])
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    # Document mistakenly inferred as RG_ANTIGO
    doc = Document(
        persona_id=persona.id,
        raw_file_name="cin_verso.png",
        sanitized_file_name="cin_verso.png",
        storage_path="path/to/cin_verso.png",
        mime_type="image/png",
        file_size_bytes=1200,
        status=DocumentStatus.NEEDS_REVIEW,
        extracted_data={
            "document_type": "RG_ANTIGO",
            "fields": {
                "rg_numero": {"value": None, "is_valid": False, "confidence": 0.0},
                "filiacao": {"value": "MAE PAI", "is_valid": True, "confidence": 0.9},
            },
            "validation_errors": ["Campo obrigatório pendente ou de baixa confiança: 'rg_numero'."],
        },
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    review_payload = {
        "template_code": "CIN",
        "corrected_data": {
            "cpf": "123.456.789-09",
            "nome_completo": "CARLOS ALBERTO FERREIRA",
            "data_nascimento": "15/05/1990",
            "naturalidade": "SÃO PAULO",
            "nacionalidade": "BRASILEIRA",
            "data_validade": "15/05/2034",
        },
        "notes": "Corrigido de RG_ANTIGO para CIN pelo operador.",
    }

    resp = await client.put(
        f"/api/v1/documents/{doc.id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "READY"
    assert data["confidence_score"] == 1.0
    assert data["extracted_data"]["document_type"] == "CIN"
    assert data["extracted_data"]["fields"]["cpf"]["value"] == "123.456.789-09"
    assert data["extracted_data"]["fields"]["nome_completo"]["value"] == "CARLOS ALBERTO FERREIRA"
    assert data["extracted_data"]["validation_errors"] == []

    # Verify persona onboarding was marked completed because CIN is now fulfilled (RN-15)
    await db_session.refresh(persona)
    assert persona.status.value == "ONBOARDING_COMPLETED"


@pytest.mark.asyncio
async def test_document_quality_rejection_rn09(
    client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test rejecting unreadable blurry document (RN-09)."""
    monkeypatch.setattr(minio_service, "generate_presigned_get_url", lambda path, **kw: "http://mock-s3/preview")
    from app.workers.tasks.webhook_tasks import dispatch_workspace_webhooks
    monkeypatch.setattr(dispatch_workspace_webhooks, "delay", lambda *a, **k: None)

    persona = Persona(name="Persona Rej")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    doc = Document(
        persona_id=persona.id,
        raw_file_name="borrado.jpg",
        sanitized_file_name="borrado.jpg",
        storage_path="path/to/borrado.jpg",
        mime_type="image/jpeg",
        file_size_bytes=800,
        status=DocumentStatus.NEEDS_REVIEW,
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    rej_payload = {
        "rejection_reason": "Foto com reflexo de luz e texto completamente ilegível. Necessário novo envio.",
    }

    resp = await client.post(
        f"/api/v1/documents/{doc.id}/reject",
        json=rej_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == rej_payload["rejection_reason"]


@pytest.mark.asyncio
async def test_public_upload_with_signed_token_rn11(
    client: AsyncClient,
    test_admin_user: User,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test public upload via ephemeral token with in-memory validation (RN-11, RN-12)."""
    monkeypatch.setattr(minio_service, "upload_bytes", lambda *a, **k: "mock-storage-path")
    from app.workers.tasks.ocr_tasks import process_document_ocr
    monkeypatch.setattr(process_document_ocr, "delay", lambda *a, **k: None)

    persona = Persona(name="Persona Pub")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    link_id = "link-12345"
    token = create_collection_link_token(
        persona_id=persona.id,
        created_by_user_id=test_admin_user.id,
        collection_link_id=link_id,
        expires_hours=48,
    )
    link = CollectionLink(
        id=link_id,
        persona_id=persona.id,
        created_by_user_id=test_admin_user.id,
        token_hash="hash123",
        max_uses=5,
    )
    db_session.add(link)
    await db_session.commit()

    image_bytes = create_test_image_bytes()
    files = {"file": ("my_cin.png", image_bytes, "image/png")}
    data = {"document_type": "CIN"}

    resp = await client.post(
        f"/api/v1/public/upload?token={token}",
        files=files,
        data=data,
    )
    assert resp.status_code == 202
    resp_data = resp.json()
    assert resp_data["status"] == "PENDING"
    assert resp_data["persona_id"] == persona.id


@pytest.mark.asyncio
async def test_list_documents_populates_preview_urls(
    client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test that GET /documents/ populates preview_url for all items in the returned list."""
    monkeypatch.setattr(minio_service, "generate_presigned_get_url", lambda path, **kw: f"http://mock-s3/preview/{path}")

    persona = Persona(name="Persona List Preview")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    doc = Document(
        persona_id=persona.id,
        raw_file_name="cin.png",
        sanitized_file_name="cin.png",
        storage_path="path/to/cin.png",
        mime_type="image/png",
        file_size_bytes=1200,
        status=DocumentStatus.READY,
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/documents/?persona_id={persona.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["preview_url"] == "http://mock-s3/preview/path/to/cin.png"


@pytest.mark.asyncio
async def test_stream_document_file_with_query_token(
    client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test that GET /documents/{id}/file supports ?token= query parameter for inline browser viewing."""
    test_image_bytes = create_test_image_bytes()
    monkeypatch.setattr(minio_service, "get_bytes", lambda path: test_image_bytes)

    persona = Persona(name="Persona Stream Query")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    doc = Document(
        persona_id=persona.id,
        raw_file_name="foto.png",
        sanitized_file_name="foto.png",
        storage_path="path/to/foto.png",
        mime_type="image/png",
        file_size_bytes=len(test_image_bytes),
        status=DocumentStatus.READY,
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()

    # Call /file without Authorization header, passing ?token=<admin_token>
    resp = await client.get(f"/api/v1/documents/{doc.id}/file?token={admin_token}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) == len(test_image_bytes)
