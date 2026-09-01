"""Template entity model defining document schema, required fields and rules."""

from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Template(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "templates"

    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    # JSON definition of expected fields (name, label, required, data_type, etc.)
    fields_schema: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    # Additional validation rules (e.g., CPF modulo 11, MRZ parity, etc.)
    validation_rules: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="template"
    )
