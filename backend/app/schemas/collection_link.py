"""Pydantic v2 schemas for Collection Links (RN-11, RN-12)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CollectionLinkCreate(BaseModel):
    persona_id: str
    expires_hours: int = Field(default=48, ge=1, le=168)  # Default 48h (RN-12)
    max_uses: int = Field(default=5, ge=1, le=50)


class CollectionLinkRead(BaseModel):
    id: str
    persona_id: str
    created_by_user_id: str
    expires_at: datetime
    max_uses: int
    uses_count: int
    is_active: bool
    is_expired: bool
    public_url: str
    token: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str
    persona_id: str
