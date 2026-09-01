"""Tests for Multilayer in-memory File Security Inspection."""

import io
import pytest
from PIL import Image

from app.core.file_security import (
    FileSecurityError,
    inspect_file_in_memory,
    sanitize_filename,
)


def create_sample_png_bytes() -> bytes:
    """Generate in-memory valid PNG image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_sample_jpeg_bytes() -> bytes:
    """Generate in-memory valid JPEG image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_sample_pdf_bytes(malicious_tag: bytes = None) -> bytes:
    """Generate minimal valid PDF bytes with optional malicious tag."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    )
    if malicious_tag:
        content += b"4 0 obj<</Type/Action/S" + malicious_tag + b"/JS (app.alert(1))>>endobj\n"
    content += (
        b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    )
    return content


def test_sanitize_filename():
    """Test filename sanitization against path traversal and dangerous characters."""
    assert sanitize_filename("../../etc/passwd.png") == "passwd.png"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.exe.jpg") == "calc.exe.jpg"
    assert sanitize_filename("doc name with spaces (1).pdf") == "doc_name_with_spaces__1_.pdf"
    assert sanitize_filename("") == "unnamed_file"


def test_valid_png_passes_security():
    """Valid PNG passes security inspection."""
    png_bytes = create_sample_png_bytes()
    mime, clean_name = inspect_file_in_memory(png_bytes, "my_document.png")
    assert mime == "image/png"
    assert clean_name == "my_document.png"


def test_valid_jpeg_passes_security():
    """Valid JPEG passes security inspection."""
    jpg_bytes = create_sample_jpeg_bytes()
    mime, clean_name = inspect_file_in_memory(jpg_bytes, "photo.jpg")
    assert mime == "image/jpeg"
    assert clean_name == "photo.jpg"


def test_disguised_executable_rejected():
    """An executable file renamed with .jpg extension is rejected by magic bytes."""
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"A" * 100
    with pytest.raises(FileSecurityError) as exc_info:
        inspect_file_in_memory(fake_exe, "malware.jpg")
    assert "Formato de arquivo não suportado" in str(exc_info.value) or "assinatura binária" in str(exc_info.value)


def test_pdf_with_javascript_rejected():
    """PDF containing /JavaScript tags is rejected by deep inspection."""
    malicious_pdf = create_sample_pdf_bytes(malicious_tag=b"/JavaScript")
    with pytest.raises(FileSecurityError) as exc_info:
        inspect_file_in_memory(malicious_pdf, "invoice.pdf")
    assert "Tag ou script executável" in str(exc_info.value) or "não seguro" in str(exc_info.value)


def test_empty_file_rejected():
    """Empty 0-byte file is rejected."""
    with pytest.raises(FileSecurityError) as exc_info:
        inspect_file_in_memory(b"", "empty.png")
    assert "vazio (0 bytes)" in str(exc_info.value)
