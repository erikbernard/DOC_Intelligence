"""Tests for Persona Completion (RN-15) and Hard Delete Cascading (RN-13)."""

from unittest.mock import MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus, UploadOrigin
from app.models.persona import Persona, PersonaStatus
from app.services.persona_service import (
    check_and_update_persona_completion,
    hard_delete_persona,
)
from app.services.storage.minio_service import minio_service


@pytest.mark.asyncio
async def test_persona_onboarding_completion_lifecycle(db_session: AsyncSession):
    """Test that persona transitions to ONBOARDING_COMPLETED when all required docs are READY (RN-15)."""
    persona = Persona(
        name="Joao Silva",
        required_document_types=["CIN", "COMPROVANTE_RESIDENCIA"],
        status=PersonaStatus.PENDING,
    )
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    # 1. Add first document (CIN) READY
    doc1 = Document(
        persona_id=persona.id,
        raw_file_name="cin.png",
        sanitized_file_name="cin.png",
        storage_path="path/to/cin.png",
        mime_type="image/png",
        file_size_bytes=1000,
        status=DocumentStatus.READY,
        extracted_data={"document_type": "CIN"},
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc1)
    await db_session.commit()

    completed = await check_and_update_persona_completion(db_session, persona.id)
    assert completed is False
    assert persona.status == PersonaStatus.PENDING

    # 2. Add second document (COMPROVANTE_RESIDENCIA) READY
    doc2 = Document(
        persona_id=persona.id,
        raw_file_name="residencia.pdf",
        sanitized_file_name="residencia.pdf",
        storage_path="path/to/residencia.pdf",
        mime_type="application/pdf",
        file_size_bytes=2000,
        status=DocumentStatus.READY,
        extracted_data={"document_type": "COMPROVANTE_RESIDENCIA"},
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc2)
    await db_session.commit()

    completed_final = await check_and_update_persona_completion(db_session, persona.id)
    assert completed_final is True
    assert persona.status == PersonaStatus.ONBOARDING_COMPLETED


@pytest.mark.asyncio
async def test_persona_hard_delete_cascades_minio_and_db(db_session: AsyncSession, monkeypatch):
    """Test that deleting persona performs hard delete in MinIO and DB (RN-13)."""
    # Mock MinIO delete operations
    mock_delete_prefix = MagicMock(return_value=2)
    mock_delete_obj = MagicMock(return_value=True)
    monkeypatch.setattr(minio_service, "delete_prefix", mock_delete_prefix)
    monkeypatch.setattr(minio_service, "delete_object", mock_delete_obj)

    persona = Persona(name="Persona To Delete")
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(persona)

    doc = Document(
        persona_id=persona.id,
        raw_file_name="doc.jpg",
        sanitized_file_name="doc.jpg",
        storage_path=f"personas/{persona.id}/CIN/doc.jpg",
        mime_type="image/jpeg",
        file_size_bytes=500,
        upload_origin=UploadOrigin.SYSTEM_USER,
    )
    db_session.add(doc)
    await db_session.commit()

    # Execute hard delete
    deleted = await hard_delete_persona(db_session, persona.id)
    assert deleted is True

    # Verify DB record is gone
    check_persona = await db_session.get(Persona, persona.id)
    assert check_persona is None

    # Verify MinIO prefix delete was called
    mock_delete_prefix.assert_called_once_with(f"personas/{persona.id}/")
