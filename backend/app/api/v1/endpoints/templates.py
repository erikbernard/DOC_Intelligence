"""Document Template CRUD endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_db
from app.models.template import Template
from app.models.user import User
from app.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate

router = APIRouter()


@router.get("/", response_model=List[TemplateRead])
async def list_templates(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """List all available document extraction templates."""
    stmt = select(Template).where(Template.is_active == True).order_by(Template.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new document schema template."""
    stmt = select(Template).where(Template.code == data.code)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um modelo (template) cadastrado com o código '{data.code}'.",
        )

    template = Template(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get template definition by ID."""
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template de documento não encontrado com o ID informado."
        )
    return template


@router.put("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Update template definition."""
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template de documento não encontrado com o ID informado."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template
