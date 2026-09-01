"""Path formatter and filename standardizer for MinIO (S3) and PostgreSQL."""

from datetime import datetime, timezone
import hashlib
import os
import re
from typing import Optional
import unicodedata


def slugify(value: Optional[str]) -> str:
    """Normalize and slugify a string for filesystem/S3 safe names (removes accents, replaces spaces)."""
    if not value:
        return ""
    # Normalize unicode characters (remove accents/cedilha)
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    # Convert to lowercase and replace non-alphanumeric chars with underscore
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return slug


def generate_standard_filename(
    persona_name: Optional[str] = None,
    persona_id: str = "",
    doc_type: str = "DOC",
    doc_id: str = "",
    original_filename: str = "document.png",
    created_at: Optional[datetime] = None,
) -> str:
    """Generate a standardized, pragmatic filename.
    Format: {tipo}_{persona}_{data}_{codigo_unico}.{ext}
    Example: cin_mateus_rodrigues_pereira_20260901_36e9bdc3.png
    """
    now = created_at or datetime.now(timezone.utc)
    _, ext = os.path.splitext(original_filename)
    clean_ext = ext.lstrip(".").lower() or "png"
    if clean_ext == "jpeg":
        clean_ext = "jpg"

    clean_type = slugify(doc_type) or "doc"
    clean_persona = slugify(persona_name) if persona_name else ""
    if not clean_persona and persona_id:
        clean_persona = f"persona_{persona_id[:8]}"
    elif not clean_persona:
        clean_persona = "titular"

    date_str = now.strftime("%Y%m%d")
    short_id = doc_id[:8] if doc_id else "00000000"

    return f"{clean_type}_{clean_persona}_{date_str}_{short_id}.{clean_ext}"


DEFAULT_STORAGE_MASK = "{doc_type}/{persona}/{data}-{cod_unico}.{ext}"


def format_storage_path(
    mask: Optional[str] = None,
    persona_name: Optional[str] = None,
    persona_id: str = "",
    doc_type: str = "DOC",
    doc_id: str = "",
    sanitized_filename: str = "file.png",
    file_bytes: Optional[bytes] = None,
    created_at: Optional[datetime] = None,
    workspace_id: Optional[str] = None,
) -> str:
    """Format storage path according to standard: tipo/persona/data-cod_unico.ext
    Supported placeholders:
      {doc_type}   - Clean document type (e.g. cin, rg, cnh)
      {persona}    - Persona slugified name or persona_id (e.g. mateus_rodrigues_pereira)
      {persona_id} - Persona UUID
      {data}       - Date in YYYYMMDD format
      {cod_unico}  - 8-char short doc id
      {short_id}   - 8-char short doc id
      {YYYY}       - 4-digit year
      {MM}         - 2-digit month
      {DD}         - 2-digit day
      {ext}        - File extension (jpg, png, pdf)
      {hash}       - 8-char sha256 hash
    """
    pattern = mask if mask and mask.strip() else DEFAULT_STORAGE_MASK
    now = created_at or datetime.now(timezone.utc)

    # Split name and extension
    name_root, ext = os.path.splitext(sanitized_filename)
    clean_ext = ext.lstrip(".").lower() or "png"
    if clean_ext == "jpeg":
        clean_ext = "jpg"
    clean_name = name_root or "document"

    clean_type = slugify(doc_type) or "doc"
    clean_persona = slugify(persona_name) if persona_name else ""
    if not clean_persona and persona_id:
        clean_persona = f"persona_{persona_id[:8]}"
    elif not clean_persona:
        clean_persona = "titular"

    short_id = doc_id[:8] if doc_id else "00000000"
    date_str = now.strftime("%Y%m%d")

    # Compute short content hash if bytes provided
    short_hash = "00000000"
    if file_bytes:
        short_hash = hashlib.sha256(file_bytes).hexdigest()[:8]

    # Map variables
    replacements = {
        "{workspace_id}": str(workspace_id or ""),
        "{persona_id}": str(persona_id),
        "{persona}": clean_persona,
        "{doc_type}": clean_type,
        "{doc_id}": str(doc_id),
        "{cod_unico}": short_id,
        "{short_id}": short_id,
        "{data}": date_str,
        "{YYYYMMDD}": date_str,
        "{YYYY}": now.strftime("%Y"),
        "{MM}": now.strftime("%m"),
        "{DD}": now.strftime("%d"),
        "{sanitized_name}": clean_name,
        "{ext}": clean_ext,
        "{hash}": short_hash,
    }

    formatted = pattern
    for var, val in replacements.items():
        formatted = formatted.replace(var, val)

    # Clean double slashes and normalize
    formatted = re.sub(r"/+", "/", formatted)
    formatted = formatted.lstrip("/")

    return formatted
