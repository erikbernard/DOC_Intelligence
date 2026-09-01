"""Multilayer in-memory file security validation.

Performs:
1. Magic Bytes / MIME real type validation
2. Filename sanitization and path traversal prevention
3. PDF embedded malicious script and macro inspection (/JavaScript, /Launch, etc.)
4. Image decompression bomb / pixel bomb prevention
5. File size limits
"""

import io
import os
import re
from typing import Tuple
from PIL import Image
import puremagic
from pypdf import PdfReader

from app.core.config import settings
from app.core.logging import app_logger

# Allowed MIME types and corresponding extensions
ALLOWED_MIME_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "application/pdf": [".pdf"],
}

# Suspicious PDF objects / actions associated with exploits
SUSPICIOUS_PDF_TAGS = [
    b"/JavaScript",
    b"/JS",
    b"/Launch",
    b"/EmbeddedFiles",
    b"/SubmitForm",
    b"/ImportData",
    b"/RichMedia",
    b"/URI",
]


class FileSecurityError(ValueError):
    """Raised when a file fails security inspection."""
    pass


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to remove path traversals and dangerous characters."""
    if not filename:
        return "unnamed_file"
    # Take only the base name
    base = os.path.basename(filename)
    # Remove null bytes and non-printable characters
    base = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", base)
    # Replace spaces and non-word chars (keeping dots and hyphens)
    clean = re.sub(r"[^\w.\-]", "_", base)
    # Prevent leading dots
    clean = clean.lstrip(".")
    if not clean:
        return "sanitized_file"
    return clean[:200]


def inspect_file_in_memory(
    file_bytes: bytes, original_filename: str
) -> Tuple[str, str]:
    """Inspect and validate a file completely in memory.

    Returns:
        Tuple[str, str]: (detected_mime_type, sanitized_filename)

    Raises:
        FileSecurityError: If the file is corrupted, malicious, or exceeds safety limits.
    """
    # 1. Check size limit
    file_size = len(file_bytes)
    if file_size == 0:
        raise FileSecurityError("O arquivo enviado está vazio (0 bytes). Por favor, selecione um arquivo válido.")
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise FileSecurityError(
            f"O tamanho do arquivo ({file_size / (1024 * 1024):.2f}MB) excede o limite máximo permitido de {settings.MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB."
        )

    clean_name = sanitize_filename(original_filename)

    # 2. Magic Bytes / Real MIME Type detection
    try:
        matches = puremagic.magic_string(file_bytes)
        if not matches:
            raise FileSecurityError("Não foi possível identificar a assinatura binária real do arquivo.")
        detected_mime = matches[0].mime_type
    except Exception as exc:
        raise FileSecurityError(f"Erro ao verificar assinatura binária do arquivo: {str(exc)}") from exc

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise FileSecurityError(
            f"Formato de arquivo não suportado: '{detected_mime}'. Por favor, envie apenas imagens JPEG, PNG ou documentos PDF."
        )

    # 3. PDF Deep Inspection
    if detected_mime == "application/pdf":
        _inspect_pdf(file_bytes)

    # 4. Image Deep Inspection (JPEG / PNG)
    elif detected_mime in ("image/jpeg", "image/png"):
        _inspect_image(file_bytes)

    app_logger.info(
        f"Inspeção de segurança aprovada para '{clean_name}', MIME: {detected_mime}, tamanho: {file_size} bytes"
    )
    return detected_mime, clean_name


def _inspect_pdf(file_bytes: bytes) -> None:
    """Inspect PDF content for malicious scripts, page limits, and corruption."""
    # Check for raw suspicious PDF action tags
    lower_bytes = file_bytes.lower()
    for tag in SUSPICIOUS_PDF_TAGS:
        if tag.lower() in lower_bytes:
            raise FileSecurityError(
                f"Tag ou script executável não seguro detectado no PDF ({tag.decode('latin1')}). Por razões de segurança, PDFs com ações embutidas são bloqueados."
            )

    # Structural PDF parsing with pypdf
    try:
        stream = io.BytesIO(file_bytes)
        reader = PdfReader(stream)
        num_pages = len(reader.pages)
        if num_pages == 0:
            raise FileSecurityError("O documento PDF enviado não contém nenhuma página válida (0 páginas).")
        if num_pages > settings.MAX_PDF_PAGES:
            raise FileSecurityError(
                f"O documento PDF excede o número máximo permitido de páginas ({num_pages} páginas detectadas, máximo permitido é {settings.MAX_PDF_PAGES})."
            )
        # Attempt extracting text/checking basic page structure
        _ = reader.pages[0]
    except Exception as exc:
        if isinstance(exc, FileSecurityError):
            raise
        raise FileSecurityError(f"Estrutura do arquivo PDF corrompida ou malformada: {str(exc)}") from exc


def _inspect_image(file_bytes: bytes) -> None:
    """Inspect image structure and verify protection against decompression bombs."""
    # Enforce decompression bomb limit in Pillow
    Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
    try:
        stream = io.BytesIO(file_bytes)
        with Image.open(stream) as img:
            img.verify()  # Verify image integrity
            # Reopen to check dimensions after verify
            stream.seek(0)
            with Image.open(stream) as img_loaded:
                width, height = img_loaded.size
                total_pixels = width * height
                if total_pixels > settings.MAX_IMAGE_PIXELS:
                    raise FileSecurityError(
                        f"As dimensões da imagem ({width}x{height} = {total_pixels} pixels) excedem o limite seguro de processamento."
                    )
    except Image.DecompressionBombError as exc:
        raise FileSecurityError(f"Imagem bloqueada por exceder limites seguros de descompressão (Pixel Bomb): {str(exc)}") from exc
    except Exception as exc:
        if isinstance(exc, FileSecurityError):
            raise
        raise FileSecurityError(f"Arquivo de imagem corrompido ou formato ilegível: {str(exc)}") from exc
