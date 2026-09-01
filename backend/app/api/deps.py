"""API Dependencies for Database, Authentication, and Authorization."""

from typing import AsyncGenerator, Dict, Any, Optional
from fastapi import Depends, HTTPException, Header, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_async_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """Extract and validate JWT Bearer token for internal System Users."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido. Por favor, realize o login para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "system_access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas ou token de acesso incompatível.",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sua sessão expirou ou o token de acesso é inválido. Por favor, faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado no sistema."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conta de usuário está inativa. Entre em contato com o suporte.",
        )
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that current authenticated user has ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito. Esta operação exige privilégios de Administrador (RN-10).",
        )
    return current_user


async def validate_public_collection_token(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Validate ephemeral signed token for public upload link (RN-11, RN-12)."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token do link de coleta é obrigatório para acessar este formulário.",
        )

    try:
        payload = decode_token(raw_token)
        token_type = payload.get("type")
        if token_type != "collection_link":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tipo de token inválido para coleta de documentos (RN-11).",
            )
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Este link de envio de documentos expirou ou é inválido. Por favor, solicite um novo link de coleta (RN-12).",
        )
