"""Celery Task for dispatching signed Webhooks with HMAC-SHA256 and retries."""

from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Any, Dict, Optional
import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import app_logger
from app.models.webhook import WebhookConfig, WebhookDeliveryLog
from app.workers.celery_app import celery_app

sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@celery_app.task(bind=True, name="app.workers.tasks.webhook_tasks.dispatch_workspace_webhooks", max_retries=4)
def dispatch_workspace_webhooks(
    self,
    workspace_id: Optional[str] = None,
    event_name: str = "document.updated",
    payload: Optional[Dict[str, Any]] = None,
    document_id: Optional[str] = None,
    persona_id: Optional[str] = None,
):
    """Dispatch HTTP POST notifications with HMAC signature to subscribed webhook endpoints."""
    payload = payload or {}
    app_logger.info(f"Dispatching webhooks for event={event_name}")
    session = SyncSessionLocal()

    try:
        stmt = (
            select(WebhookConfig)
            .where(WebhookConfig.is_active == True)
        )
        configs = session.execute(stmt).scalars().all()

        if not configs:
            app_logger.info("No active webhooks configured.")
            return {"dispatched": 0}

        dispatched = 0
        for config in configs:
            if config.subscribed_events and event_name not in config.subscribed_events:
                continue

            # Prepare payload envelope
            body_dict = {
                "event": event_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "persona_id": persona_id or payload.get("persona_id"),
                "document_id": document_id or payload.get("document_id"),
                "data": payload,
            }
            body_json = json.dumps(body_dict, default=str)
            body_bytes = body_json.encode("utf-8")

            # Generate HMAC-SHA256 signature
            signature = hmac.new(
                config.secret_key.encode("utf-8"), body_bytes, hashlib.sha256
            ).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "DOC_Intelligence-Webhook/1.0",
                "X-DocIntelligence-Signature": signature,
                "X-DocIntelligence-Event": event_name,
            }

            status_code = None
            response_text = None
            is_success = False

            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(config.target_url, content=body_bytes, headers=headers)
                    status_code = response.status_code
                    response_text = response.text[:1000]
                    is_success = response.is_success
            except Exception as http_err:
                response_text = f"Connection error: {str(http_err)}"
                app_logger.warning(f"Webhook delivery failed for '{config.target_url}': {str(http_err)}")

            # Record Delivery Log
            log = WebhookDeliveryLog(
                webhook_config_id=config.id,
                document_id=document_id or payload.get("document_id"),
                event=event_name,
                payload=body_dict,
                response_status_code=status_code,
                response_body=response_text,
                attempt_count=self.request.retries + 1,
                is_success=is_success,
            )
            session.add(log)
            session.commit()
            dispatched += 1

            if not is_success and self.request.retries < self.max_retries:
                # Retry with exponential backoff (10s, 30s, 60s, 300s)
                countdown = [10, 30, 60, 300][min(self.request.retries, 3)]
                raise self.retry(countdown=countdown)

        return {"dispatched": dispatched}

    except Exception as exc:
        session.rollback()
        app_logger.error(f"Error in dispatch_workspace_webhooks: {str(exc)}")
        raise
    finally:
        session.close()
