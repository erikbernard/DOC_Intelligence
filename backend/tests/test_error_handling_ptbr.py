"""Tests for semantic PT-BR error responses and exception handlers."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validation_error_returns_semantic_ptbr(client: AsyncClient):
    """Test that 422 validation error returns structured semantic PT-BR JSON."""
    # Send invalid email and empty payload
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "email_invalido_sem_arroba", "password": ""},
    )
    assert response.status_code == 422
    data = response.json()

    assert data["sucesso"] is False
    assert data["codigo_status"] == 422
    assert data["tipo_erro"] == "DADOS_INVALIDOS"
    assert "inconsistências" in data["mensagem"] or "inválido" in data["mensagem"]
    assert isinstance(data["detalhes"], list)
    assert len(data["detalhes"]) >= 1
    # Check that error is in Portuguese
    primeiro_erro = data["detalhes"][0]
    assert "campo" in primeiro_erro
    assert "Formato de e-mail inválido" in primeiro_erro["mensagem"] or "obrigatório" in primeiro_erro["mensagem"]


@pytest.mark.asyncio
async def test_unauthorized_error_returns_semantic_ptbr(client: AsyncClient):
    """Test that 401 unauthorized error returns structured semantic PT-BR JSON."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()

    assert data["sucesso"] is False
    assert data["codigo_status"] == 401
    assert data["tipo_erro"] == "NAO_AUTORIZADO"
    assert "Token de autenticação não fornecido" in data["mensagem"] or "login" in data["mensagem"]


@pytest.mark.asyncio
async def test_not_found_error_returns_semantic_ptbr(client: AsyncClient, admin_token: str):
    """Test that 404 not found error returns structured semantic PT-BR JSON."""
    response = await client.get(
        "/api/v1/personas/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    data = response.json()

    assert data["sucesso"] is False
    assert data["codigo_status"] == 404
    assert data["tipo_erro"] == "NAO_ENCONTRADO"
    assert "Persona não encontrada" in data["mensagem"]
