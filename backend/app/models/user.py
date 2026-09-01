"""User model for System Users (Admin and Operator)."""

import enum
from typing import List, Optional
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.OPERATOR, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    created_documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="created_by_user",
        foreign_keys="Document.created_by_user_id",
    )
    approved_documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="approved_by_user",
        foreign_keys="Document.approved_by_user_id",
    )
    created_collection_links: Mapped[List["CollectionLink"]] = relationship(
        "CollectionLink", back_populates="created_by_user"
    )
