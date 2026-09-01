"""Persona lifecycle management, onboarding completion, and hard-delete cascading."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
from app.models.document import Document, DocumentStatus
from app.models.persona import Persona, PersonaStatus
from app.services.sse_service import publish_event
from app.services.storage.minio_service import minio_service


async def check_and_update_persona_completion(
    db: AsyncSession, persona_id: str
) -> bool:
    """Evaluate if all required document types are processed and marked READY (RN-15)."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        return False

    required_types = persona.required_document_types or ["CIN"]

    # Query ready documents for this persona
    stmt = (
        select(Document.template_id, Document.status, Document.extracted_data)
        .where(Document.persona_id == persona_id)
        .where(Document.status == DocumentStatus.READY)
    )
    result = await db.execute(stmt)
    ready_docs = result.all()

    # Get processed document types
    processed_types = set()
    for doc in ready_docs:
        # Check template code or document_type in extracted_data
        data = doc.extracted_data or {}
        doc_type = data.get("document_type", "CIN")
        processed_types.add(doc_type)

    # Check if all required document types are fulfilled
    all_completed = all(req in processed_types for req in required_types)

    if all_completed and persona.status != PersonaStatus.ONBOARDING_COMPLETED:
        persona.status = PersonaStatus.ONBOARDING_COMPLETED
        await db.commit()
        await db.refresh(persona)
        app_logger.info(f"Persona '{persona_id}' completed all requirements. Status -> ONBOARDING_COMPLETED (RN-15)")

        # Publish real-time event
        publish_event(
            event_type="persona.completed",
            payload={
                "persona_id": persona.id,
                "name": persona.name,
                "status": persona.status.value,
                "required_types": required_types,
            },
            persona_id=persona.id,
        )
        return True

    return False


async def hard_delete_persona(db: AsyncSession, persona_id: str) -> bool:
    """Execute irreversible Hard Delete on PostgreSQL and MinIO S3 (RN-13 Right to be Forgotten)."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        return False

    # 1. Delete all files in MinIO storage under persona path prefix
    minio_prefix = f"personas/{persona_id}/"
    minio_service.delete_prefix(minio_prefix)

    # Also delete by specific document paths if any
    stmt = select(Document.storage_path).where(Document.persona_id == persona_id)
    result = await db.execute(stmt)
    for row in result.scalars():
        if row:
            minio_service.delete_object(row)

    # 2. Hard delete from database (cascades to documents and collection links)
    await db.delete(persona)
    await db.commit()

    app_logger.info(f"Persona '{persona_id}' completely hard-deleted from DB and MinIO (RN-13)")
    return True
