"""Tests for Pessimistic Locking service (RN-07, RN-08)."""

from unittest.mock import MagicMock
from app.services.lock_service import LockService


def test_locking_acquisition_and_conflict(monkeypatch):
    """Test that two users cannot lock the same document simultaneously (RN-07)."""
    service = LockService()
    fake_storage = {}

    # Mock Redis client
    mock_redis = MagicMock()

    def fake_set(name, value, nx=False, ex=None):
        if nx and name in fake_storage:
            return False
        fake_storage[name] = value
        return True

    def fake_get(name):
        return fake_storage.get(name)

    def fake_delete(name):
        return fake_storage.pop(name, None) is not None

    mock_redis.set.side_effect = fake_set
    mock_redis.get.side_effect = fake_get
    mock_redis.delete.side_effect = fake_delete

    service.redis_client = mock_redis

    # User 1 acquires lock
    acquired1, lock1 = service.acquire_lock("doc-1", "user-1", "User One")
    assert acquired1 is True

    # User 2 tries to acquire lock on same document -> Conflict (RN-07)
    acquired2, lock2 = service.acquire_lock("doc-1", "user-2", "User Two")
    assert acquired2 is False
    assert lock2["user_name"] == "User One"

    # User 1 releases lock
    released = service.release_lock("doc-1", "user-1")
    assert released is True

    # Now User 2 can acquire lock
    acquired3, lock3 = service.acquire_lock("doc-1", "user-2", "User Two")
    assert acquired3 is True
