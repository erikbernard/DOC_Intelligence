"""Pydantic v2 schemas for Webhook configuration and delivery."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WebhookConfigBase(BaseModel):
    target_url: str = Field(..., max_length=500)
    secret_key: str = Field(..., min_length=16, max_length=255)
    subscribed_events: List[str] = Field(
        default_factory=lambda: [
            "document.ready",
            "document.needs_review",
            "document.failed",
            "document.rejected",
            "persona.completed",
        ]
    )
    is_active: bool = True


class WebhookConfigCreate(WebhookConfigBase):
    pass


class WebhookConfigUpdate(BaseModel):
    target_url: Optional[str] = None
    secret_key: Optional[str] = None
    subscribed_events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookConfigRead(WebhookConfigBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookPayload(BaseModel):
    event: str
    timestamp: datetime
    document_id: Optional[str] = None
    persona_id: Optional[str] = None
    data: Dict[str, Any]


class WebhookDeliveryLogRead(BaseModel):
    id: str
    webhook_config_id: str
    document_id: Optional[str] = None
    event: str
    payload: Dict[str, Any]
    response_status_code: Optional[int] = None
    attempt_count: int
    is_success: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
