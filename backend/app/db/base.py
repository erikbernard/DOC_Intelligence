"""SQLAlchemy 2.0 Declarative Base with UUIDs and Timestamps."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return current UTC timezone-aware timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all database models."""
    pass


class TimestampMixin:
    """Reusable mixin for created_at and updated_at timestamp columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Reusable mixin for UUID v4 primary keys."""
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
