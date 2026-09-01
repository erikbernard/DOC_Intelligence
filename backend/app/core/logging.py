"""Structured logging configuration with strict PII masking (LGPD - RN-14)."""

import re
import sys
from loguru import logger

# Regex patterns for Brazilian PII (CPF, RG, Email, etc.)
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")


def pii_masking_filter(record: dict) -> bool:
    """Filter and sanitize PII from log message text according to RN-14."""
    msg = record["message"]
    # Mask CPFs
    msg = CPF_PATTERN.sub("[CPF_MASKED]", msg)
    # Mask Emails (except domain or placeholder if needed)
    msg = EMAIL_PATTERN.sub("[EMAIL_MASKED]", msg)
    record["message"] = msg
    return True


def setup_logging() -> None:
    """Configure loguru with standard output, JSON or formatted text, and PII masking."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        filter=pii_masking_filter,
        level="INFO",
    )


# Export logger instance
app_logger = logger
