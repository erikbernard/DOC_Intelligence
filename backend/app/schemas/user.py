"""Pydantic v2 schemas for User and Authentication."""

from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.user import UserRole

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z0-9\.\-_]{2,}$")


def validate_and_clean_email(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("O e-mail deve ser uma sequência de texto válida.")
    clean = v.strip().lower()
    if not EMAIL_REGEX.match(clean):
        raise ValueError(
            "Formato de e-mail inválido. Por favor, utilize um endereço no formato usuario@empresa.com."
        )
    return clean


class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.OPERATOR
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_and_clean_email(v)


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("A senha deve conter no mínimo 6 caracteres.")
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @field_validator("email")
    @classmethod
    def check_email_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_and_clean_email(v)
        return v


class UserRead(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserRead


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_and_clean_email(v)
