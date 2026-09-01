"""Webhook Configuration and Delivery Logs endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_db
from app.models.user import User
from app.models.webhook import WebhookConfig, WebhookDeliveryLog
from app.schemas.webhook import (
    WebhookConfigCreate,
    WebhookConfigRead,
    WebhookConfigUpdate,
    WebhookDeliveryLogRead,
)

router = APIRouter()


@router.get("/", response_model=List[WebhookConfigRead])
async def list_webhook_configs(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """List configured webhooks."""
    stmt = select(WebhookConfig).order_by(WebhookConfig.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=WebhookConfigRead, status_code=status.HTTP_201_CREATED)
async def create_webhook_config(
    data: WebhookConfigCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new webhook subscription endpoint."""
    config = WebhookConfig(**data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/{config_id}", response_model=WebhookConfigRead)
async def get_webhook_config(
    config_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get webhook configuration by ID."""
    config = await db.get(WebhookConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuração de Webhook não encontrada com o ID informado."
        )
    return config


@router.put("/{config_id}", response_model=WebhookConfigRead)
async def update_webhook_config(
    config_id: str,
    data: WebhookConfigUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Update webhook subscription settings."""
    config = await db.get(WebhookConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuração de Webhook não encontrada com o ID informado."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_config(
    config_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a webhook subscription."""
    config = await db.get(WebhookConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuração de Webhook não encontrada com o ID informado."
        )
    await db.delete(config)
    await db.commit()
    return None


@router.get("/{config_id}/logs", response_model=List[WebhookDeliveryLogRead])
async def list_webhook_delivery_logs(
    config_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """List recent delivery logs and response statuses for a webhook."""
    stmt = (
        select(WebhookDeliveryLog)
        .where(WebhookDeliveryLog.webhook_config_id == config_id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
