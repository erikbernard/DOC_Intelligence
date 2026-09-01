"""Integration tests for FastAPI API Endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_auth_login_and_me(client: AsyncClient, test_admin_user: User):
    """Test login endpoint returning token and accessing /me."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_admin_user.email, "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token = data["access_token"]

    # Call /me with token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_admin_user.email


@pytest.mark.asyncio
async def test_persona_creation_and_listing(client: AsyncClient, admin_token: str):
    """Test creating a persona directly and listing personas."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create persona directly
    per_resp = await client.post(
        "/api/v1/personas/",
        json={
            "name": "Maria Silva",
            "email": "maria@example.com",
            "required_document_types": ["CIN"],
        },
        headers=headers,
    )
    assert per_resp.status_code == 201
    per_data = per_resp.json()
    assert per_data["name"] == "Maria Silva"
    assert "id" in per_data

    # List personas
    list_resp = await client.get("/api/v1/personas/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_collection_link_generation(client: AsyncClient, admin_token: str):
    """Test generating a secure ephemeral collection link (RN-11, RN-12)."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create persona
    per_resp = await client.post(
        "/api/v1/personas/",
        json={"name": "Candidato Link"},
        headers=headers,
    )
    per_id = per_resp.json()["id"]

    # Generate collection link
    link_resp = await client.post(
        "/api/v1/collection-links/",
        json={"persona_id": per_id, "expires_hours": 48},
        headers=headers,
    )
    assert link_resp.status_code == 201
    link_data = link_resp.json()
    assert "token" in link_data
    assert link_data["max_uses"] == 5
    assert link_data["uses_count"] == 0
    assert link_data["is_expired"] is False
