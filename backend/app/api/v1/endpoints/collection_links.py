"""Collection Links endpoints for generating secure public onboarding links (RN-11, RN-12)."""

from datetime import datetime, timezone
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_db
from app.core.config import settings
from app.core.security import create_collection_link_token
from app.models.collection_link import CollectionLink
from app.models.persona import Persona
from app.models.user import User
from app.schemas.collection_link import CollectionLinkCreate, CollectionLinkRead

router = APIRouter()


def is_datetime_expired(dt: datetime) -> bool:
    if dt is None:
        return False
    if dt.tzinfo is None:
        return dt < datetime.utcnow()
    return dt < datetime.now(timezone.utc)


@router.post("/", response_model=CollectionLinkRead, status_code=status.HTTP_201_CREATED)
async def generate_collection_link(
    data: CollectionLinkCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a secure, signed public link for document upload (expires in 48h - RN-12)."""
    persona = await db.get(Persona, data.persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona não encontrada com o ID informado.",
        )

    # Temporary ID to embed in token
    import uuid
    link_id = str(uuid.uuid4())

    token = create_collection_link_token(
        persona_id=data.persona_id,
        created_by_user_id=current_user.id,
        collection_link_id=link_id,
        expires_hours=data.expires_hours,
    )
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    link = CollectionLink(
        id=link_id,
        persona_id=data.persona_id,
        created_by_user_id=current_user.id,
        token_hash=token_hash,
        max_uses=data.max_uses,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    public_url = f"/onboarding/upload?token={token}"
    is_expired = is_datetime_expired(link.expires_at)

    return CollectionLinkRead(
        id=link.id,
        persona_id=link.persona_id,
        created_by_user_id=link.created_by_user_id,
        expires_at=link.expires_at,
        max_uses=link.max_uses,
        uses_count=link.uses_count,
        is_active=link.is_active,
        is_expired=is_expired,
        public_url=public_url,
        token=token,
        created_at=link.created_at,
    )


@router.get("/{link_id}", response_model=CollectionLinkRead)
async def get_collection_link_status(
    link_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve collection link usage and expiration state."""
    link = await db.get(CollectionLink, link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link de coleta não encontrado com o ID informado."
        )

    is_expired = is_datetime_expired(link.expires_at)
    return CollectionLinkRead(
        id=link.id,
        persona_id=link.persona_id,
        created_by_user_id=link.created_by_user_id,
        expires_at=link.expires_at,
        max_uses=link.max_uses,
        uses_count=link.uses_count,
        is_active=link.is_active,
        is_expired=is_expired,
        public_url=f"/onboarding/upload?token_id={link.id}",
        token="[MASKED]",
        created_at=link.created_at,
    )
