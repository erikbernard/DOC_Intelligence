"""Old Brazilian RG (Registro Geral) Document Parser."""

import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.models.document import DocumentStatus
from app.services.ocr.base import OCRRawResult
from app.services.ocr.parsers.base import BaseDocumentParser, ParsedDocumentResult

RG_REGEX = re.compile(r"\b(\d{1,2}\.?\d{3}\.?\d{3}[-\.]?[\dXx]|\d{7,9})\b")
DATE_REGEX = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")


class RGDocumentParser(BaseDocumentParser):
    """Parser for the traditional/legacy Brazilian RG document."""

    @property
    def document_type(self) -> str:
        return "RG_ANTIGO"

    def parse(
        self, raw_ocr: OCRRawResult, template_config: Optional[Dict[str, Any]] = None
    ) -> ParsedDocumentResult:
        full_text = raw_ocr.full_text

        extracted_fields: Dict[str, Any] = {
            "rg_numero": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "nome_completo": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "filiacao": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "data_nascimento": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": False, "is_fuzzy_corrected": False, "warning": None},
            "naturalidade": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": True, "is_fuzzy_corrected": False, "warning": None},
            "orgao_emissor": {"value": None, "raw_value": None, "confidence": 0.0, "is_valid": True, "is_fuzzy_corrected": False, "warning": None},
        }

        validation_errors: List[str] = []

        # 1. RG Number
        for line in raw_ocr.lines:
            match = RG_REGEX.search(line.text)
            if match and len(line.text.replace(".", "").replace("-", "").strip()) >= 7:
                extracted_fields["rg_numero"]["value"] = match.group(1)
                extracted_fields["rg_numero"]["raw_value"] = line.text.strip()
                extracted_fields["rg_numero"]["confidence"] = line.confidence
                extracted_fields["rg_numero"]["is_valid"] = True
                break

        # 2. Dates
        for line in raw_ocr.lines:
            match = DATE_REGEX.search(line.text)
            if match:
                extracted_fields["data_nascimento"]["value"] = match.group(1)
                extracted_fields["data_nascimento"]["raw_value"] = line.text.strip()
                extracted_fields["data_nascimento"]["confidence"] = line.confidence
                extracted_fields["data_nascimento"]["is_valid"] = True
                break

        # 3. Nome
        for i, line in enumerate(raw_ocr.lines):
            if "NOME" in line.text.upper() and i + 1 < len(raw_ocr.lines):
                next_line = raw_ocr.lines[i + 1]
                extracted_fields["nome_completo"]["value"] = next_line.text.strip().upper()
                extracted_fields["nome_completo"]["raw_value"] = next_line.text.strip()
                extracted_fields["nome_completo"]["confidence"] = next_line.confidence
                extracted_fields["nome_completo"]["is_valid"] = True
                break

        # 4. Filiação (Mandatory for RG Antigo - RN-05)
        for i, line in enumerate(raw_ocr.lines):
            if "FILIA" in line.text.upper() and i + 1 < len(raw_ocr.lines):
                filiacao_lines = [raw_ocr.lines[i + 1].text.strip()]
                if i + 2 < len(raw_ocr.lines):
                    filiacao_lines.append(raw_ocr.lines[i + 2].text.strip())
                val = " / ".join(filiacao_lines)
                extracted_fields["filiacao"]["value"] = val
                extracted_fields["filiacao"]["raw_value"] = val
                extracted_fields["filiacao"]["confidence"] = raw_ocr.lines[i + 1].confidence
                extracted_fields["filiacao"]["is_valid"] = True
                break

        # Calculate Overall Confidence
        field_confidences = [
            f["confidence"] for f in extracted_fields.values() if f["value"] is not None
        ]
        overall_confidence = (
            sum(field_confidences) / len(field_confidences) if field_confidences else 0.0
        )

        mandatory_keys = ["rg_numero", "nome_completo", "filiacao", "data_nascimento"]
        is_auto_approved = True
        for key in mandatory_keys:
            f = extracted_fields[key]
            if not f["value"] or not f["is_valid"] or f["confidence"] < settings.OCR_CONFIDENCE_THRESHOLD:
                is_auto_approved = False
                validation_errors.append(f"Campo obrigatório pendente ou de baixa confiança: '{key}'.")

        status = DocumentStatus.READY if is_auto_approved else DocumentStatus.NEEDS_REVIEW

        return ParsedDocumentResult(
            document_type=self.document_type,
            status=status,
            overall_confidence=round(overall_confidence, 4),
            extracted_fields=extracted_fields,
            validation_errors=validation_errors,
            is_auto_approved=is_auto_approved,
            raw_text=full_text,
        )
