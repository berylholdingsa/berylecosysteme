"""Integration tests for public auth routes and protected AOQ routes."""

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from src.config.settings import settings


@pytest.mark.asyncio
async def test_login_is_public(async_client):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


@pytest.mark.asyncio
async def test_register_is_public(async_client):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


@pytest.mark.asyncio
async def test_aoq_requires_token(async_client):
    response = await async_client.get("/api/v1/aoq/rules")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_aoq_accepts_valid_token(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    class FakeService:
        def list_rules(self):
            return []

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.get(
        "/api/v1/aoq/rules",
        headers={"Authorization": valid_tokens["social"]},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_aoq_rejects_expired_token(async_client):
    expired_claims = {
        "sub": "social_123",
        "scopes": ["social"],
        "domain": "social",
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
    }
    expired_token = jwt.encode(
        expired_claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await async_client.get(
        "/api/v1/aoq/rules",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"
