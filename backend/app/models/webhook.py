"""Webhook configuration and delivery log models."""

from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WebhookConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "webhook_configs"

    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False)
    subscribed_events: Mapped[List[str]] = mapped_column(
        JSON,
        default=lambda: [
            "document.ready",
            "document.needs_review",
            "document.failed",
            "document.rejected",
            "persona.completed",
        ],
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    delivery_logs: Mapped[List["WebhookDeliveryLog"]] = relationship(
        "WebhookDeliveryLog", back_populates="webhook_config", cascade="all, delete-orphan"
    )


class WebhookDeliveryLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "webhook_delivery_logs"

    webhook_config_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("webhook_configs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    webhook_config: Mapped["WebhookConfig"] = relationship(
        "WebhookConfig", back_populates="delivery_logs"
    )
