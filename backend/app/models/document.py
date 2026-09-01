"""Document entity model storing metadata, OCR results, and lifecycle states."""

import enum
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"  # High confidence and valid identifiers
    NEEDS_REVIEW = "NEEDS_REVIEW"  # Low confidence (<85%), missing field, or invalid checksum (RN-01, RN-04)
    TEMPLATE_NOT_IDENTIFIED = "TEMPLATE_NOT_IDENTIFIED"  # Template deduction confidence < 90% (RN-02)
    REJECTED = "REJECTED"  # Rejected due to unreadable / blurry quality by reviewer (RN-09)
    FAILED = "FAILED"  # Error in processing / corrupted


class UploadOrigin(str, enum.Enum):
    SYSTEM_USER = "SYSTEM_USER"
    PUBLIC_LINK = "PUBLIC_LINK"


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    persona_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("templates.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    raw_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sanitized_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING, index=True, nullable=False
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    extracted_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    raw_ocr_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Concurrency Lock (Pessimistic Locking - RN-07 / RN-08)
    locked_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    locked_by_user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    lock_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # User Attribution & Provenance
    upload_origin: Mapped[UploadOrigin] = mapped_column(
        Enum(UploadOrigin), default=UploadOrigin.SYSTEM_USER, nullable=False
    )
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    collection_link_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("collection_links.id", ondelete="SET NULL"), nullable=True
    )
    upload_ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    upload_user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Approval Audit (RN-10)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    persona: Mapped["Persona"] = relationship("Persona", back_populates="documents")
    template: Mapped[Optional["Template"]] = relationship("Template", back_populates="documents")
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="created_documents", foreign_keys=[created_by_user_id]
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="approved_documents", foreign_keys=[approved_by_user_id]
    )
    collection_link: Mapped[Optional["CollectionLink"]] = relationship(
        "CollectionLink", back_populates="documents"
    )
