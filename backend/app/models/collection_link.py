"""CollectionLink model for ephemeral public document upload links (RN-11, RN-12)."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


def default_collection_link_expiry() -> datetime:
    """Return default expiration of 48 hours from now (RN-12)."""
    return datetime.now(timezone.utc) + timedelta(hours=48)


class CollectionLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "collection_links"

    persona_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("personas.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=default_collection_link_expiry, nullable=False
    )
    max_uses: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    uses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    persona: Mapped["Persona"] = relationship("Persona", back_populates="collection_links")
    created_by_user: Mapped["User"] = relationship(
        "User", back_populates="created_collection_links"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="collection_link"
    )
