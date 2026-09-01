"""Security, hashing and JWT token utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash from plain text."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any],
    role: str = "OPERATOR",
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a standard JWT access token for System Users."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "role": role,
        "type": "system_access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_collection_link_token(
    persona_id: str,
    created_by_user_id: str,
    collection_link_id: str,
    expires_hours: int = 48,
) -> str:
    """Create an ephemeral signed JWT token for public document collection links (RN-11, RN-12)."""
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode = {
        "sub": str(persona_id),
        "persona_id": str(persona_id),
        "created_by_user_id": str(created_by_user_id),
        "collection_link_id": str(collection_link_id),
        "type": "collection_link",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token signature and expiration."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid or expired token: {str(exc)}") from exc
