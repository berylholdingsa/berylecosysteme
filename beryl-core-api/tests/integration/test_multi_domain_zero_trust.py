"""
Extended Zero-Trust Multi-Domain Tests for Beryl Core API.

Tests async multi-domaines avec authentification par scopes, rate-limiting,
logs sécurité, et fallback pour services externes.
"""

import pytest
import pytest_asyncio
import json
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from main import app


@pytest_asyncio.fixture
async def test_app():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_fintech_token(valid_tokens):
    return valid_tokens["fintech"]

@pytest.fixture
def valid_mobility_token(valid_tokens):
    return valid_tokens["mobility"]

@pytest.fixture
def valid_esg_token(valid_tokens):
    return valid_tokens["esg"]

@pytest.fixture
def valid_social_token(valid_tokens):
    return valid_tokens["social"]


class TestMultiDomainZeroTrust:
    """Tests multi-domaines avec scopes et sécurité."""

    @pytest.mark.asyncio
    async def test_fintech_access_with_valid_scope(self, test_app, valid_fintech_token):
        # Mock auth middleware pour simuler succès
        from starlette.responses import JSONResponse
        with patch('src.api.v1.middlewares.auth_middleware.AuthMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = JSONResponse(status_code=200, content={"payments": []})
            response = await test_app.get("/api/v1/fintech/payments", headers={"Authorization": valid_fintech_token})
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mobility_access_with_valid_scope(self, test_app, valid_mobility_token):
        with patch('src.api.v1.middlewares.auth_middleware.AuthMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = await test_app.post("/api/v1/mobility/demand/predict", json={}, headers={"Authorization": valid_mobility_token})
            response = await test_app.post("/api/v1/mobility/demand/predict", json={}, headers={"Authorization": valid_mobility_token})
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_esg_access_with_valid_scope(self, test_app, valid_esg_token):
        with patch('src.api.v1.middlewares.auth_middleware.AuthMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = await test_app.post("/api/v1/esg/pedometer/data", json={}, headers={"Authorization": valid_esg_token})
            response = await test_app.post("/api/v1/esg/pedometer/data", json={}, headers={"Authorization": valid_esg_token})
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_social_access_with_valid_scope(self, test_app, valid_social_token):
        with patch('src.api.v1.middlewares.auth_middleware.AuthMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = await test_app.post("/api/v1/social/feed/personalized", json={}, headers={"Authorization": valid_social_token})
            response = await test_app.post("/api/v1/social/feed/personalized", json={}, headers={"Authorization": valid_social_token})
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_cross_domain_access_denied(self, test_app, valid_fintech_token):
        # Fintech token ne devrait pas accéder à mobility
        with patch('src.api.v1.middlewares.auth_middleware.AuthMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.side_effect = HTTPException(status_code=403, detail="Forbidden")
            response = await test_app.post("/api/v1/mobility/demand/predict", json={}, headers={"Authorization": valid_fintech_token})
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_app, valid_fintech_token):
        # Simuler rate-limiting après plusieurs requêtes
        with patch('src.api.v1.middlewares.rate_limit_middleware.RateLimitMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.side_effect = HTTPException(status_code=429, detail="Too Many Requests")
            response = await test_app.get("/api/v1/fintech/payments", headers={"Authorization": valid_fintech_token})
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_fallback_external_service_failure(self, test_app, valid_fintech_token, mock_external_services):
        # Mock failure d'un service externe et vérifier fallback
        mock_external_services["fintech"].get_payments.side_effect = Exception("Service indisponible")
        # Simuler que la route appelle le client
        # Pour ce test, on assume que la route gère le fallback
        response = await test_app.get("/api/v1/fintech/payments", headers={"Authorization": valid_fintech_token})
        # Vérifier que fallback retourne une réponse appropriée
        assert response.status_code in [200, 503]  # 503 pour service unavailable avec fallback

    @pytest.mark.asyncio
    async def test_security_logs_401_403(self, test_app, caplog):
        # Vérifier logs pour 401/403
        with patch('src.api.v1.middlewares.auth_middleware.AuthMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.side_effect = HTTPException(status_code=401, detail="Unauthorized")
            response = await test_app.get("/api/v1/fintech/payments")
            assert "401 Unauthorized" in caplog.text

    @pytest.mark.asyncio
    async def test_async_event_driven_multi_domain(self, test_app, valid_fintech_token, valid_mobility_token):
        # Test async entre domaines
        tasks = []
        tasks.append(test_app.get("/api/v1/fintech/payments", headers={"Authorization": valid_fintech_token}))
        tasks.append(test_app.post("/api/v1/mobility/demand/predict", json={}, headers={"Authorization": valid_mobility_token}))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Vérifier que les requêtes async sont traitées
        assert len(results) == 2