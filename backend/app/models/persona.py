"""Persona model representing an applicant/individual profile undergoing onboarding."""

import enum
from typing import Any, Dict, List, Optional
from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PersonaStatus(str, enum.Enum):
    PENDING = "PENDING"
    ONBOARDING_COMPLETED = "ONBOARDING_COMPLETED"  # RN-15


class Persona(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "personas"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[PersonaStatus] = mapped_column(
        Enum(PersonaStatus), default=PersonaStatus.PENDING, nullable=False
    )
    required_document_types: Mapped[List[str]] = mapped_column(
        JSON, default=lambda: ["CIN"], nullable=False
    )
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="persona", cascade="all, delete-orphan"
    )
    collection_links: Mapped[List["CollectionLink"]] = relationship(
        "CollectionLink", back_populates="persona", cascade="all, delete-orphan"
    )
