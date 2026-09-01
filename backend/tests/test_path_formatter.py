"""Tests for MinIO custom storage path formatting."""

from datetime import datetime, timezone

from app.services.storage.path_formatter import format_storage_path


def test_default_storage_path_formatting():
    fixed_time = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)
    path = format_storage_path(
        mask=None,
        persona_id="per-456",
        doc_type="cin",
        doc_id="doc-789",
        sanitized_filename="documento.png",
        created_at=fixed_time,
    )
    assert path == "personas/per-456/CIN/2026/08/doc-789_documento.png"


def test_custom_mask_with_hash():
    fixed_time = datetime(2026, 12, 25, 0, 0, 0, tzinfo=timezone.utc)
    custom_mask = "archive/{workspace_id}/{YYYY}/{MM}/{DD}/{doc_type}_{hash}_{sanitized_name}.{ext}"
    sample_bytes = b"Hello Document Intelligence"

    path = format_storage_path(
        mask=custom_mask,
        workspace_id="ws-abc",
        persona_id="per-def",
        doc_type="cnh",
        doc_id="doc-001",
        sanitized_filename="cnh_frente.pdf",
        file_bytes=sample_bytes,
        created_at=fixed_time,
    )
    assert path.startswith("archive/ws-abc/2026/12/25/CNH_")
    assert path.endswith("_cnh_frente.pdf")
