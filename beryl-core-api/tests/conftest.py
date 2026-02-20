"""Conftest for async fixtures in Beryl Core API tests."""

import os
import signal
import sys
import pathlib

os.environ["TESTING"] = "1"
for flag in ("TRACING_ENABLED", "METRICS_ENABLED", "AUDIT_ENABLED"):
    os.environ.setdefault(flag, "false")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.main import app


@pytest_asyncio.fixture
async def async_client():
    """Async client fixture for FastAPI tests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_tokens():
    """Fixture with valid tokens for all domains."""
    from jose import jwt
    from src.config.settings import settings
    return {
        "fintech": (
            f"Bearer {jwt.encode({'sub': 'fintech_123', 'scopes': ['fintech'], 'domain': 'fintech'}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}"
        ),
        "mobility": (
            f"Bearer {jwt.encode({'sub': 'mobility_123', 'scopes': ['mobility'], 'domain': 'mobility'}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}"
        ),
        "esg": (
            f"Bearer {jwt.encode({'sub': 'esg_123', 'scopes': ['esg'], 'domain': 'esg'}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}"
        ),
        "social": (
            f"Bearer {jwt.encode({'sub': 'social_123', 'scopes': ['social'], 'domain': 'social'}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}"
        ),
    }


@pytest.fixture
def invalid_token():
    """Invalid token fixture."""
    return "Bearer invalid.token.here"


@pytest_asyncio.fixture
async def mock_external_services():
    """Mock external services for fallback testing."""
    from unittest.mock import patch

    with patch('src.adapters.fintech_mamba_core.client.FintechClient.call_external') as fintech_mock, \
         patch('src.adapters.mobility_ai_engine.client.MobilityClient.call_external') as mobility_mock, \
         patch('src.adapters.esg_community_wb.client.ESGClient.call_external') as esg_mock, \
         patch('src.adapters.social_community_ai.client.SocialClient.call_external') as social_mock:
        yield {
            "fintech": fintech_mock,
            "mobility": mobility_mock,
            "esg": esg_mock,
            "social": social_mock
        }


PYTEST_TIMEOUT_SIGNAL = getattr(signal, "SIGALRM", None)


def _timeout_handler(signum, frame):
    raise TimeoutError("Test exceeded configured timeout")


def pytest_addoption(parser):
    parser.addini("timeout", "Maximum per-test duration in seconds", default="15")


def pytest_runtest_setup(item):
    timeout_value = int(item.config.getini("timeout") or 0)
    if PYTEST_TIMEOUT_SIGNAL and timeout_value > 0:
        signal.signal(PYTEST_TIMEOUT_SIGNAL, _timeout_handler)
        signal.alarm(timeout_value)


def pytest_runtest_teardown(item, nextitem):
    if PYTEST_TIMEOUT_SIGNAL:
        signal.alarm(0)
