"""Celery Task for asynchronous OCR processing and pipeline orchestration."""

from datetime import datetime, timezone
import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import app_logger
from app.models.document import Document, DocumentStatus
from app.models.persona import Persona, PersonaStatus
from app.models.template import Template
from app.services.ocr.context import ocr_context
from app.services.sse_service import publish_event
from app.services.storage.minio_service import minio_service
from app.workers.celery_app import celery_app
from app.workers.tasks.webhook_tasks import dispatch_workspace_webhooks

# Synchronous engine for Celery tasks
sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@celery_app.task(bind=True, name="app.workers.tasks.ocr_tasks.process_document_ocr", max_retries=2)
def process_document_ocr(self, document_id: str):
    """Asynchronously process document image/PDF via OCR context and save structured result."""
    app_logger.info(f"Starting Celery OCR task for document_id={document_id}")
    session = SyncSessionLocal()

    try:
        doc = session.get(Document, document_id)
        if not doc:
            app_logger.error(f"Document not found: {document_id}")
            return {"error": "Document not found"}

        # 1. Update status to PROCESSING and emit SSE
        doc.status = DocumentStatus.PROCESSING
        session.commit()
        session.refresh(doc)

        publish_event(
            event_type="document.processing",
            payload={
                "document_id": doc.id,
                "persona_id": doc.persona_id,
                "status": doc.status.value,
            },
            persona_id=doc.persona_id,
        )

        # 2. Get Template code if assigned
        template_code = None
        template_config = None
        if doc.template_id:
            template = session.get(Template, doc.template_id)
            if template:
                template_code = template.code
                template_config = {
                    "fields_schema": template.fields_schema,
                    "validation_rules": template.validation_rules,
                }

        # 3. Retrieve raw file bytes from MinIO
        file_bytes = minio_service.get_bytes(doc.storage_path)

        # 4. Execute OCR Pipeline (rasterize 300 DPI if PDF, OpenCV preprocess, EasyOCR, and CIN Parser)
        parsed_result, raw_ocr = ocr_context.process_document(
            file_bytes=file_bytes,
            mime_type=doc.mime_type,
            template_code=template_code,
            template_config=template_config,
        )

        # 5. Persist Results in Database
        doc.status = parsed_result.status
        doc.confidence_score = parsed_result.overall_confidence
        doc.extracted_data = {
            "document_type": parsed_result.document_type,
            "fields": parsed_result.extracted_fields,
            "validation_errors": parsed_result.validation_errors,
            "is_auto_approved": parsed_result.is_auto_approved,
        }
        doc.raw_ocr_data = {
            "engine": raw_ocr.engine_name,
            "processing_time_ms": raw_ocr.processing_time_ms,
            "full_text": raw_ocr.full_text,
            "lines_count": len(raw_ocr.lines),
        }

        # If template was dynamically deduced, link template if exists
        if not doc.template_id and parsed_result.document_type != "UNKNOWN":
            matched_template = session.execute(
                select(Template).where(Template.code == parsed_result.document_type)
            ).scalar_one_or_none()
            if matched_template:
                doc.template_id = matched_template.id

        session.commit()
        session.refresh(doc)

        app_logger.info(
            f"OCR processing completed for doc_id={doc.id}, status={doc.status.value}, confidence={doc.confidence_score}"
        )

        # 6. Check Persona Onboarding Completion (RN-15)
        if doc.status == DocumentStatus.READY:
            persona = session.get(Persona, doc.persona_id)
            if persona:
                required_types = persona.required_document_types or ["CIN"]
                ready_docs = session.execute(
                    select(Document)
                    .where(Document.persona_id == persona.id)
                    .where(Document.status == DocumentStatus.READY)
                ).scalars().all()

                processed_types = {
                    d.extracted_data.get("document_type", "CIN") for d in ready_docs
                }
                if all(req in processed_types for req in required_types):
                    persona.status = PersonaStatus.ONBOARDING_COMPLETED
                    session.commit()
                    publish_event(
                        event_type="persona.completed",
                        payload={
                            "persona_id": persona.id,
                            "name": persona.name,
                            "status": persona.status.value,
                        },
                        persona_id=persona.id,
                    )

        # 7. Publish Event via SSE and Webhooks
        event_name = f"document.{doc.status.value.lower()}"
        event_payload = {
            "document_id": doc.id,
            "persona_id": doc.persona_id,
            "status": doc.status.value,
            "confidence_score": doc.confidence_score,
            "extracted_data": doc.extracted_data,
        }

        publish_event(
            event_type=event_name,
            payload=event_payload,
            persona_id=doc.persona_id,
        )

        # Dispatch Webhooks
        dispatch_workspace_webhooks.delay(
            event_name=event_name,
            payload=event_payload,
            document_id=doc.id,
            persona_id=doc.persona_id,
        )

        return {
            "document_id": doc.id,
            "status": doc.status.value,
            "confidence_score": doc.confidence_score,
        }

    except Exception as exc:
        session.rollback()
        app_logger.error(f"Error during Celery OCR processing for doc_id={document_id}: {str(exc)}")

        # Update Document to FAILED
        try:
            doc = session.get(Document, document_id)
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.failure_reason = str(exc)
                session.commit()

                # Notify failure via SSE and Webhooks
                fail_payload = {
                    "document_id": doc.id,
                    "persona_id": doc.persona_id,
                    "status": "FAILED",
                    "failure_reason": str(exc),
                }
                publish_event(
                    event_type="document.failed",
                    payload=fail_payload,
                    persona_id=doc.persona_id,
                )
                dispatch_workspace_webhooks.delay(
                    event_name="document.failed",
                    payload=fail_payload,
                    document_id=doc.id,
                    persona_id=doc.persona_id,
                )
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=10)

    finally:
        session.close()
