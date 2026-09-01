"""Redis-backed Pessimistic Locking Service for Review Queue (RN-07, RN-08)."""

from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, Optional, Tuple
import redis

from app.core.config import settings
from app.core.logging import app_logger


class LockService:
    """Handles pessimistic concurrency locks with TTL in Redis."""

    def __init__(self) -> None:
        self.redis_client = redis.Redis.from_url(
            settings.redis_connection_url, decode_responses=True
        )

    def _lock_key(self, doc_id: str) -> str:
        return f"lock:doc:{doc_id}"

    def acquire_lock(
        self,
        doc_id: str,
        user_id: str,
        user_name: str,
        session_id: str = "",
        ttl_seconds: int = settings.LOCK_TTL_SECONDS,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try to acquire a pessimistic lock for review on a document.

        Returns:
            Tuple[bool, Optional[dict]]: (acquired, existing_lock_info_if_failed)
        """
        key = self._lock_key(doc_id)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        lock_data = {
            "user_id": str(user_id),
            "user_name": user_name,
            "session_id": session_id,
            "locked_at": now.isoformat(),
            "lock_expires_at": expires_at.isoformat(),
        }
        lock_json = json.dumps(lock_data)

        try:
            # SET key value NX EX ttl
            acquired = self.redis_client.set(key, lock_json, nx=True, ex=ttl_seconds)

            if acquired:
                app_logger.info(f"Pessimistic lock acquired on doc '{doc_id}' by user '{user_id}' for {ttl_seconds}s")
                return True, lock_data

            # If not acquired, check who holds it
            existing_val = self.redis_client.get(key)
            existing_data = json.loads(existing_val) if existing_val else None

            # If the same user holds it, allow renewal
            if existing_data and existing_data.get("user_id") == str(user_id):
                self.redis_client.set(key, lock_json, ex=ttl_seconds)
                return True, lock_data

            app_logger.warning(
                f"Lock conflict on doc '{doc_id}': held by {existing_data.get('user_name') if existing_data else 'unknown'}"
            )
            return False, existing_data
        except Exception as exc:
            app_logger.warning(f"Redis lock acquisition error (fallback allow): {str(exc)}")
            return True, lock_data

    def refresh_lock(
        self, doc_id: str, user_id: str, ttl_seconds: int = settings.LOCK_TTL_SECONDS
    ) -> bool:
        """Renew the TTL of an active lock if owned by the requesting user."""
        key = self._lock_key(doc_id)
        try:
            existing_val = self.redis_client.get(key)
            if not existing_val:
                return False

            data = json.loads(existing_val)
            if data.get("user_id") == str(user_id):
                now = datetime.now(timezone.utc)
                data["lock_expires_at"] = (now + timedelta(seconds=ttl_seconds)).isoformat()
                self.redis_client.set(key, json.dumps(data), ex=ttl_seconds)
                return True
            return False
        except Exception as exc:
            app_logger.warning(f"Redis lock refresh warning: {str(exc)}")
            return True

    def release_lock(
        self, doc_id: str, user_id: str, is_admin: bool = False
    ) -> bool:
        """Release the pessimistic lock if owned by user or if admin overrides."""
        key = self._lock_key(doc_id)
        try:
            existing_val = self.redis_client.get(key)
            if not existing_val:
                return True

            data = json.loads(existing_val)
            if is_admin or data.get("user_id") == str(user_id):
                self.redis_client.delete(key)
                app_logger.info(f"Lock released for doc '{doc_id}' by user '{user_id}' (admin={is_admin})")
                return True
            return False
        except Exception as exc:
            app_logger.warning(f"Redis lock release warning: {str(exc)}")
            return True

    def get_lock_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get current lock details if locked."""
        key = self._lock_key(doc_id)
        try:
            val = self.redis_client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception:
            return None


# Global singleton instance
lock_service = LockService()
