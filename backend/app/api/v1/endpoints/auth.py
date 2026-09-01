"""Authentication endpoints (Login and Profile)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserRead

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Authenticate system user via email and password, returning JWT."""
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos. Por favor, verifique suas credenciais de acesso.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conta está desativada. Entre em contato com o administrador do sistema.",
        )

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserRead.model_validate(user),
    )


@router.post("/login/form", response_model=Token, include_in_schema=False)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    """OAuth2 Form compatible login endpoint for Swagger UI."""
    clean_username = form_data.username.strip().lower()
    stmt = select(User).where(User.email == clean_username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos. Por favor, verifique suas credenciais de acesso.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conta está desativada. Entre em contato com o administrador do sistema.",
        )

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
async def read_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Return currently authenticated user profile."""
    return current_user
