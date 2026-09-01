"""Pydantic v2 schemas for Document and OCR extractions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus, UploadOrigin


class ExtractedFieldDetail(BaseModel):
    value: Optional[str] = None
    raw_value: Optional[str] = None
    confidence: float = 0.0
    is_valid: bool = True
    is_fuzzy_corrected: bool = False
    warning: Optional[str] = None


class DocumentRead(BaseModel):
    id: str
    persona_id: str
    template_id: Optional[str] = None
    raw_file_name: str
    sanitized_file_name: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    confidence_score: Optional[float] = None
    locked_by_user_id: Optional[str] = None
    locked_by_user_name: Optional[str] = None
    locked_at: Optional[datetime] = None
    lock_expires_at: Optional[datetime] = None
    upload_origin: UploadOrigin
    created_at: datetime
    updated_at: datetime
    preview_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailRead(DocumentRead):
    storage_path: str
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    raw_ocr_data: Dict[str, Any] = Field(default_factory=dict)
    failure_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_by_user_id: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    preview_url: Optional[str] = None  # Secure authenticated preview endpoint or presigned URL


class DocumentReviewUpdate(BaseModel):
    """Payload submitted by reviewer to approve / correct document data (PUT /documents/{id}/review - RN-10)."""
    corrected_data: Dict[str, Any] = Field(default_factory=dict, description="Map of field names to corrected values")
    template_code: Optional[str] = Field(None, description="Código do template desejado (ex: 'CIN', 'RG_ANTIGO', 'CNH') caso o OCR tenha inferido o template incorreto.")
    template_id: Optional[str] = Field(None, description="ID do template desejado.")
    document_type: Optional[str] = Field(None, description="Tipo do documento (ex: 'CIN', 'RG_ANTIGO').")
    notes: Optional[str] = None


class DocumentRejectRequest(BaseModel):
    """Payload for rejecting blurry / unreadable documents (RN-09)."""
    rejection_reason: str = Field(..., min_length=5, max_length=500)


class DocumentLockResponse(BaseModel):
    document_id: str
    locked: bool
    locked_by_user_id: Optional[str] = None
    locked_by_user_name: Optional[str] = None
    locked_at: Optional[datetime] = None
    lock_expires_at: Optional[datetime] = None
    message: str


class DocumentFilterParams(BaseModel):
    status: Optional[DocumentStatus] = None
    template_id: Optional[str] = None
    persona_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    in_review: Optional[bool] = None
