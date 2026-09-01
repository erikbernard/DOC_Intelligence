"""Audit service to persist audit trail records."""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
from app.models.audit import AuditLog


async def record_audit_log(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Create and persist an immutable audit log record."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    app_logger.info(f"Audit log recorded: {action} on {entity_type}:{entity_id} by user {user_id or 'anonymous'}")
    return audit
