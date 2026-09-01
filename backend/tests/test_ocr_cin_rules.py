"""Tests for CIN OCR Parser and Business Rules (RN-01 to RN-05)."""

from validate_docbr import CPF

from app.models.document import DocumentStatus
from app.services.ocr.base import OCRLineResult, OCRRawResult
from app.services.ocr.parsers.cin_parser import CINDocumentParser


def test_cin_parser_successful_auto_approval():
    """All mandatory fields present with confidence >= 85% and valid CPF -> READY (RN-01, RN-04)."""
    parser = CINDocumentParser()
    valid_cpf = CPF().generate(mask=True)

    raw_ocr = OCRRawResult(
        engine_name="TestEngine",
        lines=[
            OCRLineResult(text="REPÚBLICA FEDERATIVA DO BRASIL", confidence=0.98),
            OCRLineResult(text="CARTEIRA DE IDENTIDADE NACIONAL", confidence=0.99),
            OCRLineResult(text="NOME", confidence=0.95),
            OCRLineResult(text="CARLOS EDUARDO DA SILVA", confidence=0.96),
            OCRLineResult(text=f"CPF {valid_cpf}", confidence=0.94),
            OCRLineResult(text="NASCIMENTO 15/05/1990", confidence=0.92),
            OCRLineResult(text="SÃO PAULO", confidence=0.90),
            OCRLineResult(text="VALIDADE 15/05/2034", confidence=0.91),
        ],
        full_text="REPÚBLICA FEDERATIVA DO BRASIL\nCARTEIRA DE IDENTIDADE NACIONAL\nNOME\nCARLOS EDUARDO DA SILVA\nCPF 123...\nNASCIMENTO 15/05/1990\nSÃO PAULO\nVALIDADE 15/05/2034",
    )

    result = parser.parse(raw_ocr)

    assert result.status == DocumentStatus.READY
    assert result.is_auto_approved is True
    assert result.overall_confidence >= 0.85
    assert result.extracted_fields["cpf"]["is_valid"] is True
    assert result.extracted_fields["nome_completo"]["value"] == "CARLOS EDUARDO DA SILVA"
    assert result.extracted_fields["data_nascimento"]["value"] == "15/05/1990"


def test_cin_parser_invalid_cpf_checksum_fails_rn04():
    """Invalid CPF modulo 11 fails validation, voids confidence and moves to NEEDS_REVIEW (RN-04)."""
    parser = CINDocumentParser()
    invalid_cpf = "123.456.789-00"  # Invalid check digits

    raw_ocr = OCRRawResult(
        engine_name="TestEngine",
        lines=[
            OCRLineResult(text="CARTEIRA DE IDENTIDADE NACIONAL", confidence=0.99),
            OCRLineResult(text="NOME", confidence=0.95),
            OCRLineResult(text="MARIA HELENA SANTOS", confidence=0.96),
            OCRLineResult(text=f"CPF {invalid_cpf}", confidence=0.99),  # High visual confidence
            OCRLineResult(text="NASCIMENTO 20/10/1988", confidence=0.95),
        ],
        full_text="CARTEIRA DE IDENTIDADE NACIONAL\nNOME\nMARIA HELENA SANTOS\nCPF 123.456.789-00\nNASCIMENTO 20/10/1988",
    )

    result = parser.parse(raw_ocr)

    assert result.status == DocumentStatus.NEEDS_REVIEW
    assert result.is_auto_approved is False
    assert result.extracted_fields["cpf"]["is_valid"] is False
    assert result.extracted_fields["cpf"]["confidence"] == 0.0
    assert "Dígito verificador do CPF inválido" in result.extracted_fields["cpf"]["warning"]


def test_cin_parser_low_confidence_triggers_needs_review_rn01():
    """Field confidence below 85% moves document to NEEDS_REVIEW (RN-01)."""
    parser = CINDocumentParser()
    valid_cpf = CPF().generate(mask=True)

    raw_ocr = OCRRawResult(
        engine_name="TestEngine",
        lines=[
            OCRLineResult(text="CARTEIRA DE IDENTIDADE NACIONAL", confidence=0.99),
            OCRLineResult(text="NOME", confidence=0.95),
            OCRLineResult(text="ANA BEATRIZ SOUZA", confidence=0.72),  # Low confidence (< 85%)
            OCRLineResult(text=f"CPF {valid_cpf}", confidence=0.95),
            OCRLineResult(text="NASCIMENTO 12/03/1995", confidence=0.90),
        ],
        full_text="CARTEIRA DE IDENTIDADE NACIONAL\nNOME\nANA BEATRIZ SOUZA\nCPF ...\nNASCIMENTO 12/03/1995",
    )

    result = parser.parse(raw_ocr)

    assert result.status == DocumentStatus.NEEDS_REVIEW
    assert result.is_auto_approved is False
    assert any("abaixo do limiar seguro" in err for err in result.validation_errors)


def test_cin_parser_fuzzy_city_correction_rn03():
    """Fuzzy Levenshtein matching auto-corrects city between 80% and 99% similarity (RN-03)."""
    parser = CINDocumentParser()
    valid_cpf = CPF().generate(mask=True)

    raw_ocr = OCRRawResult(
        engine_name="TestEngine",
        lines=[
            OCRLineResult(text="CARTEIRA DE IDENTIDADE NACIONAL", confidence=0.99),
            OCRLineResult(text="NOME", confidence=0.95),
            OCRLineResult(text="PEDRO ALVARES", confidence=0.95),
            OCRLineResult(text=f"CPF {valid_cpf}", confidence=0.95),
            OCRLineResult(text="NASCIMENTO 01/01/1990", confidence=0.95),
            OCRLineResult(text="S4O PAU10", confidence=0.88),  # OCR typo for SÃO PAULO
        ],
        full_text="CARTEIRA DE IDENTIDADE NACIONAL\nNOME\nPEDRO ALVARES\nS4O PAU10",
    )

    result = parser.parse(raw_ocr)

    naturalidade_field = result.extracted_fields["naturalidade"]
    assert naturalidade_field["value"] == "SÃO PAULO"
    assert naturalidade_field["is_fuzzy_corrected"] is True
    assert naturalidade_field["raw_value"] == "S4O PAU10"


def test_ocr_context_low_confidence_deduction_routes_to_needs_review():
    """When template deduction confidence is below 90% (e.g. 0.45 or 0.80), OCRContext extracts fields and sets NEEDS_REVIEW (RN-01, RN-02)."""
    from app.services.ocr.context import OCRContext
    import io
    from PIL import Image

    ctx = OCRContext()
    # Mock engine extract to simulate 0.45 score on CIN
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(255, 255, 255)).save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # Create synthetic raw ocr result with 0.45 score (contains only "CARTEIRA DE IDENTIDADE NACIONAL")
    valid_cpf = CPF().generate(mask=True)
    fake_raw = OCRRawResult(
        engine_name="EasyOCRAdapter",
        processing_time_ms=150.0,
        lines=[
            OCRLineResult(text="IDENTIDADE NACIONAL", confidence=0.70),
            OCRLineResult(text="MARCOS TESTE", confidence=0.88),
            OCRLineResult(text=f"CPF {valid_cpf}", confidence=0.90),
        ],
        full_text=f"IDENTIDADE NACIONAL\nMARCOS TESTE\nCPF {valid_cpf}",
    )

    ctx._engine.extract = lambda img: fake_raw

    parsed_result, raw_ocr = ctx.process_document(file_bytes=img_bytes, mime_type="image/png")

    assert parsed_result.document_type == "CIN"
    assert parsed_result.status == DocumentStatus.NEEDS_REVIEW
    assert parsed_result.is_auto_approved is False
    assert len(parsed_result.extracted_fields) > 0
    assert any("abaixo do limiar" in err or "Fila de Conferência" in err for err in parsed_result.validation_errors)
