"""Base parser interface for structuring OCR results."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.models.document import DocumentStatus
from app.services.ocr.base import OCRRawResult


class ParsedDocumentResult(BaseModel):
    document_type: str
    status: DocumentStatus
    overall_confidence: float
    extracted_fields: Dict[str, Any]  # Maps field_name -> ExtractedFieldDetail dict
    validation_errors: list[str] = []
    is_auto_approved: bool = False
    raw_text: str = ""


class BaseDocumentParser(ABC):
    """Abstract parser translating raw OCR lines into structured business fields."""

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Target document type code (e.g. 'CIN', 'RG_ANTIGO')."""
        pass

    @abstractmethod
    def parse(
        self, raw_ocr: OCRRawResult, template_config: Optional[Dict[str, Any]] = None
    ) -> ParsedDocumentResult:
        """Parse raw OCR lines into structured fields and evaluate business rules."""
        pass
