"""Pydantic v2 schemas for Persona."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.persona import PersonaStatus
from app.schemas.user import validate_and_clean_email


class PersonaBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    required_document_types: List[str] = Field(default_factory=lambda: ["CIN"])
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_and_clean_email(v)
        return v


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[PersonaStatus] = None
    required_document_types: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None

    @field_validator("email")
    @classmethod
    def check_email_optional(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_and_clean_email(v)
        return v


class PersonaRead(PersonaBase):
    id: str
    status: PersonaStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonaDetailRead(PersonaRead):
    documents_count: int = 0
    ready_documents_count: int = 0
    is_onboarding_completed: bool = False
