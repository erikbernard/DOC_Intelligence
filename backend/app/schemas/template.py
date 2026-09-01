"""Pydantic v2 schemas for Template."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TemplateFieldSchema(BaseModel):
    name: str
    label: str
    data_type: str = "string"  # string, date, number
    required: bool = True
    min_confidence: float = 0.85
    validation_regex: Optional[str] = None
    description: Optional[str] = None


class TemplateBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    document_type: str = Field(..., min_length=2, max_length=50)
    fields_schema: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    fields_schema: Optional[List[Dict[str, Any]]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemplateRead(TemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
