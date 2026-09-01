"""Tests for MockOCREngineAdapter and .env strategy switching."""

import io
import pytest
from PIL import Image

from app.core.config import settings
from app.models.document import DocumentStatus
from app.services.ocr.adapters.mock_ocr_adapter import MockOCREngineAdapter
from app.services.ocr.context import OCRContext, get_configured_engine


def create_dummy_png_bytes() -> bytes:
    """Generate a minimal valid PNG image."""
    img = Image.new("RGB", (20, 20), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_mock_ocr_deterministic_failure_ratio():
    """Verify that in a batch of 10 images, exactly 8 are auto-approved (READY)

    and exactly 2 are routed to manual review (NEEDS_REVIEW).
    """
    mock_adapter = MockOCREngineAdapter()
    mock_adapter.reset_counter()
    ctx = OCRContext(default_engine=mock_adapter)

    img_bytes = create_dummy_png_bytes()
    results = []

    for _ in range(10):
        parsed, raw = ctx.process_document(img_bytes, mime_type="image/png")
        results.append(parsed)

    # Count statuses
    ready_count = sum(1 for p in results if p.status == DocumentStatus.READY)
    needs_review_count = sum(1 for p in results if p.status == DocumentStatus.NEEDS_REVIEW)

    assert ready_count == 8, f"Expected 8 READY documents, got {ready_count}"
    assert needs_review_count == 2, f"Expected 2 NEEDS_REVIEW documents, got {needs_review_count}"

    # Verify specific failure indices
    assert results[4].status == DocumentStatus.NEEDS_REVIEW
    assert any("CPF" in err for err in results[4].validation_errors)

    assert results[9].status == DocumentStatus.NEEDS_REVIEW
    assert any("Confiança" in err or "obrigatório" in err or "Template" in err for err in results[9].validation_errors)


def test_mock_ocr_repeats_cycle_smoothly():
    """Verify that the counter wraps around 10 smoothly for 20 documents (16 ready, 4 review)."""
    mock_adapter = MockOCREngineAdapter()
    mock_adapter.reset_counter()
    ctx = OCRContext(default_engine=mock_adapter)

    img_bytes = create_dummy_png_bytes()
    results = [ctx.process_document(img_bytes, mime_type="image/png")[0] for _ in range(20)]

    ready_count = sum(1 for p in results if p.status == DocumentStatus.READY)
    review_count = sum(1 for p in results if p.status == DocumentStatus.NEEDS_REVIEW)

    assert ready_count == 16
    assert review_count == 4


def test_get_configured_engine_switch(monkeypatch):
    """Test dynamic switching between 'mock' and 'easyocr' via settings.OCR_ENGINE."""
    monkeypatch.setattr(settings, "OCR_ENGINE", "mock")
    engine = get_configured_engine()
    assert isinstance(engine, MockOCREngineAdapter)
    assert engine.engine_name == "MockOCR_v1"

    monkeypatch.setattr(settings, "OCR_ENGINE", "easyocr")
    engine2 = get_configured_engine()
    assert engine2.engine_name == "EasyOCR_v1"
