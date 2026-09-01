"""OCR Context (Strategy Manager & Orchestration Pipeline).

Handles:
- PDF in-memory rasterization at 300 DPI via pypdfium2 (RN-06)
- OCR Strategy selection (EasyOCR default)
- Dynamic Template Deduction with 90% confidence threshold (RN-02)
- Execution of document parser (CIN / RG) and business validation
"""

import io
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image
import pypdfium2 as pdfium

from app.core.config import settings
from app.core.logging import app_logger
from app.models.document import DocumentStatus
from app.services.ocr.adapters.easyocr_adapter import EasyOCREngineAdapter
from app.services.ocr.base import BaseOCREngine, OCRRawResult
from app.services.ocr.parsers.base import BaseDocumentParser, ParsedDocumentResult
from app.services.ocr.parsers.cin_parser import CINDocumentParser
from app.services.ocr.parsers.rg_parser import RGDocumentParser
from app.services.ocr.preprocessor import bytes_to_numpy


def rasterize_pdf_to_images(
    pdf_bytes: bytes, dpi: int = settings.PDF_RASTERIZE_DPI
) -> List[np.ndarray]:
    """Rasterize PDF pages in memory at specified DPI (RN-06: 300 DPI standard)."""
    images: List[np.ndarray] = []
    pdf = pdfium.PdfDocument(pdf_bytes)
    scale = dpi / 72.0  # 72 is standard PDF point resolution

    for page_idx in range(len(pdf)):
        page = pdf[page_idx]
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        # Convert PIL to OpenCV BGR numpy array
        rgb_np = np.array(pil_image)
        if len(rgb_np.shape) == 3 and rgb_np.shape[2] == 3:
            bgr_np = rgb_np[:, :, ::-1]
        elif len(rgb_np.shape) == 2:
            bgr_np = cv2.cvtColor(rgb_np, cv2.COLOR_GRAY2BGR)
        else:
            bgr_np = rgb_np[:, :, :3][:, :, ::-1]
        images.append(bgr_np)

    app_logger.info(f"Rasterized PDF into {len(images)} page images at {dpi} DPI")
    return images


def get_configured_engine() -> BaseOCREngine:
    """Instantiate OCR Engine according to settings.OCR_ENGINE ('easyocr' or 'mock')."""
    engine_type = (getattr(settings, "OCR_ENGINE", "easyocr") or "easyocr").lower().strip()
    if engine_type in ("mock", "mockocr", "ocrmock"):
        from app.services.ocr.adapters.mock_ocr_adapter import MockOCREngineAdapter

        app_logger.info("Using MockOCREngineAdapter (configured via OCR_ENGINE in .env)")
        return MockOCREngineAdapter()

    from app.services.ocr.adapters.easyocr_adapter import EasyOCREngineAdapter

    app_logger.info("Using EasyOCREngineAdapter (configured via OCR_ENGINE in .env)")
    return EasyOCREngineAdapter()


class OCRContext:
    """Orchestrator context holding the active OCR Engine Strategy and Parsers."""

    def __init__(self, default_engine: Optional[BaseOCREngine] = None) -> None:
        self._engine: BaseOCREngine = default_engine or get_configured_engine()
        self._parsers: Dict[str, BaseDocumentParser] = {
            "CIN": CINDocumentParser(),
            "RG_ANTIGO": RGDocumentParser(),
        }

    def set_engine(self, engine: BaseOCREngine) -> None:
        """Dynamically switch the OCR Engine Strategy at runtime."""
        app_logger.info(f"Switching OCR Engine Strategy to: {engine.engine_name}")
        self._engine = engine

    def register_parser(self, parser: BaseDocumentParser) -> None:
        """Register a new specialized document parser."""
        self._parsers[parser.document_type] = parser

    def deduce_template(self, full_text: str) -> Tuple[Optional[str], float]:
        """Deduce template based on textual cues and layout patterns (RN-02)."""
        text_upper = full_text.upper()

        cin_score = 0.0
        rg_score = 0.0

        # CIN indicators
        if "CARTEIRA DE IDENTIDADE NACIONAL" in text_upper or "IDENTIDADE NACIONAL" in text_upper:
            cin_score += 0.50
        if "REPÚBLICA FEDERATIVA DO BRASIL" in text_upper:
            cin_score += 0.25
        if "CPF" in text_upper:
            cin_score += 0.20
        if "VALIDADE" in text_upper:
            cin_score += 0.10

        # RG Antigo indicators
        if "REGISTRO GERAL" in text_upper:
            rg_score += 0.50
        if "SECRETARIA DE SEGURANÇA" in text_upper or "SSP" in text_upper:
            rg_score += 0.30
        if "FILIAÇÃO" in text_upper:
            rg_score += 0.30

        if cin_score >= rg_score and cin_score > 0:
            return "CIN", min(cin_score, 1.0)
        elif rg_score > cin_score:
            return "RG_ANTIGO", min(rg_score, 1.0)
        return None, 0.0

    def process_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        template_code: Optional[str] = None,
        template_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ParsedDocumentResult, OCRRawResult]:
        """Execute complete OCR pipeline from file bytes to structured parsed result."""
        # 1. Obtain image matrices (rasterize if PDF)
        try:
            if mime_type == "application/pdf":
                page_images = rasterize_pdf_to_images(file_bytes, dpi=settings.PDF_RASTERIZE_DPI)
                if not page_images:
                    raise ValueError("PDF does not contain any renderable pages.")
                main_image_np = page_images[0]
            else:
                main_image_np = bytes_to_numpy(file_bytes)
        except Exception:
            from app.services.ocr.adapters.mock_ocr_adapter import MockOCREngineAdapter
            if isinstance(self._engine, MockOCREngineAdapter):
                main_image_np = np.zeros((100, 100, 3), dtype=np.uint8)
            else:
                raise

        # 2. Execute OCR Engine Strategy
        raw_ocr_result = self._engine.extract(main_image_np)

        # 3. Handle Template Selection / Dynamic Deduction (RN-02)
        target_template = template_code
        deduction_warning = None

        if not target_template:
            deduced_type, deduction_conf = self.deduce_template(raw_ocr_result.full_text)
            app_logger.info(f"Deduced template '{deduced_type}' with confidence {deduction_conf:.2f}")

            if deduced_type:
                target_template = deduced_type
                if deduction_conf < settings.TEMPLATE_DEDUCTION_THRESHOLD:
                    deduction_warning = (
                        f"Template '{deduced_type}' deduzido com confiança de {deduction_conf * 100:.0f}% "
                        f"(abaixo do limiar de auto-aprovação de {settings.TEMPLATE_DEDUCTION_THRESHOLD * 100:.0f}%). "
                        "Encaminhado para Fila de Conferência (RN-01, RN-02)."
                    )
            else:
                # Default fallback to CIN parser
                target_template = "CIN"
                deduction_warning = "Tipo de documento não identificado automaticamente com alta confiança. Processado com modelo padrão CIN para conferência."

        # 4. Dispatch to specialized Parser
        parser = self._parsers.get(target_template) or self._parsers.get("CIN")

        parsed_result = parser.parse(raw_ocr_result, template_config=template_config)

        # If deduction had a warning, ensure status is at most NEEDS_REVIEW and record warning
        if deduction_warning:
            parsed_result.validation_errors.append(deduction_warning)
            if parsed_result.status == DocumentStatus.READY:
                parsed_result.status = DocumentStatus.NEEDS_REVIEW
                parsed_result.is_auto_approved = False

        return parsed_result, raw_ocr_result


# Singleton OCR Context instance
ocr_context = OCRContext()
