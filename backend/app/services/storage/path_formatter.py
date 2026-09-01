"""Path formatter for custom storage masks in MinIO (S3)."""

from datetime import datetime, timezone
import hashlib
import os
import re
from typing import Optional

DEFAULT_STORAGE_MASK = "personas/{persona_id}/{doc_type}/{YYYY}/{MM}/{doc_id}_{sanitized_name}.{ext}"


def format_storage_path(
    mask: Optional[str] = None,
    persona_id: str = "",
    doc_type: str = "DOC",
    doc_id: str = "",
    sanitized_filename: str = "file.png",
    file_bytes: Optional[bytes] = None,
    created_at: Optional[datetime] = None,
    workspace_id: Optional[str] = None,
) -> str:
    """Format custom storage path using template variables.

    Supported placeholders:
      {persona_id}     - Persona UUID
      {doc_type}       - Document Type (e.g. CIN, CNH, RG)
      {doc_id}         - Document UUID
      {YYYY}           - 4-digit Year
      {MM}             - 2-digit Month
      {DD}             - 2-digit Day
      {sanitized_name} - Base file name without extension
      {ext}            - File extension without dot (e.g. jpg, png, pdf)
      {hash}           - First 8 chars of SHA256 of file bytes
    """
    pattern = mask if mask and mask.strip() else DEFAULT_STORAGE_MASK
    now = created_at or datetime.now(timezone.utc)

    # Split name and extension
    name_root, ext = os.path.splitext(sanitized_filename)
    clean_ext = ext.lstrip(".").lower() or "bin"
    clean_name = name_root or "document"

    # Compute short content hash if bytes provided
    short_hash = "00000000"
    if file_bytes:
        short_hash = hashlib.sha256(file_bytes).hexdigest()[:8]

    # Map variables
    replacements = {
        "{workspace_id}": str(workspace_id or ""),
        "{persona_id}": str(persona_id),
        "{doc_type}": str(doc_type).upper(),
        "{doc_id}": str(doc_id),
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
