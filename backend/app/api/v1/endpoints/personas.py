"""Persona CRUD and Lifecycle endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_db
from app.models.document import Document, DocumentStatus
from app.models.persona import Persona, PersonaStatus
from app.models.user import User
from app.schemas.persona import (
    PersonaCreate,
    PersonaDetailRead,
    PersonaRead,
    PersonaUpdate,
)
from app.services.persona_service import hard_delete_persona

router = APIRouter()


@router.get("/", response_model=List[PersonaRead])
async def list_personas(
    status_filter: Optional[PersonaStatus] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """List personas with optional status filter."""
    stmt = select(Persona)
    if status_filter:
        stmt = stmt.where(Persona.status == status_filter)

    stmt = stmt.order_by(Persona.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
async def create_persona(
    data: PersonaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new applicant Persona profile."""
    persona = Persona(**data.model_dump())
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return persona


@router.get("/{persona_id}", response_model=PersonaDetailRead)
async def get_persona_detail(
    persona_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed Persona profile including document completion metrics."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona não encontrada com o ID informado."
        )

    # Count documents
    stmt_total = select(func.count()).select_from(Document).where(Document.persona_id == persona_id)
    total_docs = (await db.execute(stmt_total)).scalar() or 0

    stmt_ready = (
        select(func.count())
        .select_from(Document)
        .where(Document.persona_id == persona_id)
        .where(Document.status == DocumentStatus.READY)
    )
    ready_docs = (await db.execute(stmt_ready)).scalar() or 0

    return PersonaDetailRead(
        id=persona.id,
        name=persona.name,
        email=persona.email,
        cpf=persona.cpf,
        phone=persona.phone,
        status=persona.status,
        required_document_types=persona.required_document_types,
        extra_metadata=persona.extra_metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        documents_count=total_docs,
        ready_documents_count=ready_docs,
        is_onboarding_completed=(persona.status == PersonaStatus.ONBOARDING_COMPLETED),
    )


@router.put("/{persona_id}", response_model=PersonaRead)
async def update_persona(
    persona_id: str,
    data: PersonaUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Update persona profile."""
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona não encontrada com o ID informado."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(persona, field, value)

    await db.commit()
    await db.refresh(persona)
    return persona


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Irreversible Hard Delete of Persona and all its files from MinIO & PostgreSQL (RN-13)."""
    success = await hard_delete_persona(db, persona_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona não encontrada com o ID informado."
        )
    return None
