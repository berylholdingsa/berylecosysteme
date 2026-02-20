"""Integration tests for J3-J5 mobility/security/esg backend changes."""

from __future__ import annotations

import hashlib
import hmac
import time
from uuid import uuid4

import pytest

from src.config.settings import settings


def _secure_headers(authorization: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": authorization,
        "X-Correlation-ID": str(uuid4()),
        "X-Nonce": str(uuid4()),
        "X-Timestamp": str(int(time.time())),
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


@pytest.mark.asyncio
async def test_token_exchange_success(async_client, monkeypatch):
    import src.api.v1.routes.auth_routes as auth_routes

    monkeypatch.setattr(auth_routes, "verify_id_token", lambda token: {"uid": "firebase-user-123"})

    response = await async_client.post(
        "/api/v1/auth/token-exchange",
        json={"firebase_id_token": "fake-firebase-token-for-tests"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert "mobility" in payload["scopes"]


@pytest.mark.asyncio
async def test_signature_challenge_verify_and_replay_block(async_client, valid_tokens):
    payload_hash = hashlib.sha256(b"payload-for-signature").hexdigest()
    challenge_response = await async_client.post(
        "/api/v1/security/signature/challenge",
        headers=_secure_headers(valid_tokens["social"], "sig-challenge-1"),
        json={"scope": "ride.book", "payload_hash": payload_hash},
    )
    assert challenge_response.status_code == 201
    challenge = challenge_response.json()

    rotation_window_seconds = max(60, settings.nonce_ttl_seconds)
    window = challenge["timestamp"] // rotation_window_seconds
    rotated_secret = hmac.new(
        settings.event_hmac_secret.encode("utf-8"),
        f"signature-window:{window}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    canonical_payload = (
        f"{challenge['challenge_id']}:{challenge['nonce']}:{challenge['timestamp']}:{payload_hash}:ride.book"
    )
    signature = hmac.new(
        rotated_secret.encode("utf-8"),
        canonical_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    verify_response = await async_client.post(
        "/api/v1/security/signature/verify",
        headers=_secure_headers(valid_tokens["social"], "sig-verify-1"),
        json={
            "challenge_id": challenge["challenge_id"],
            "payload_hash": payload_hash,
            "signature": signature,
        },
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["verified"] is True

    replay_response = await async_client.post(
        "/api/v1/security/signature/verify",
        headers=_secure_headers(valid_tokens["social"], "sig-verify-2"),
        json={
            "challenge_id": challenge["challenge_id"],
            "payload_hash": payload_hash,
            "signature": signature,
        },
    )
    assert replay_response.status_code == 409
    replay_payload = replay_response.json()
    assert replay_payload["code"] == "SECURITY_REPLAY_DETECTED"
    assert replay_payload["correlation_id"]


@pytest.mark.asyncio
async def test_mobility_ride_lifecycle(async_client, valid_tokens):
    quote_response = await async_client.post(
        "/api/v1/mobility/ride/quote",
        headers=_secure_headers(valid_tokens["mobility"], "ride-quote-1"),
        json={
            "rider_id": "mobility_123",
            "pickup_label": "5.345,-4.024",
            "dropoff_label": "5.372,-4.011",
            "service_tier": "standard",
        },
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    assert quote["pricing_model_version"]
    assert quote["confidence_interval"]["lower"] <= quote["estimated_price_xof"] <= quote["confidence_interval"]["upper"]
    assert quote["explainability"]["summary"]

    book_response = await async_client.post(
        "/api/v1/mobility/ride/book",
        headers=_secure_headers(valid_tokens["mobility"], "ride-book-1"),
        json={"quote_id": quote["quote_id"], "rider_id": "mobility_123"},
    )
    assert book_response.status_code == 200
    ride = book_response.json()
    assert ride["status"] == "BOOKED"

    assign_response = await async_client.post(
        "/api/v1/mobility/ride/assign",
        headers=_secure_headers(valid_tokens["mobility"], "ride-assign-1"),
        json={"ride_id": ride["ride_id"], "driver_id": "driver-test-1"},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "ASSIGNED"

    complete_response = await async_client.post(
        "/api/v1/mobility/ride/complete",
        headers=_secure_headers(valid_tokens["mobility"], "ride-complete-1"),
        json={"ride_id": ride["ride_id"], "duration_minutes": 22, "distance_km": 6.4},
    )
    assert complete_response.status_code == 200
    completed_ride = complete_response.json()
    assert completed_ride["status"] == "COMPLETED"
    assert completed_ride["final_price_xof"] is not None

    read_response = await async_client.get(
        f"/api/v1/mobility/ride/{ride['ride_id']}",
        headers={
            "Authorization": valid_tokens["mobility"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert read_response.status_code == 200
    assert read_response.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_esg_compute_endpoint(async_client, valid_tokens):
    response = await async_client.post(
        "/api/v1/esg/score/compute",
        headers=_secure_headers(valid_tokens["esg"], "esg-compute-1"),
        json={
            "user_id": "esg_123",
            "period": "monthly",
            "city": "Abidjan",
            "profile": "mobile",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["score"] >= 0
    assert payload["class"] in {"A", "B", "C", "D"}
    assert payload["calculation_hash"]
    assert payload["model_version"].startswith("esg-v2")


@pytest.mark.asyncio
async def test_unified_error_model_when_idempotency_missing(async_client, valid_tokens):
    response = await async_client.post(
        "/api/v1/mobility/ride/quote",
        headers=_secure_headers(valid_tokens["mobility"]),
        json={
            "rider_id": "mobility_123",
            "pickup_label": "Cocody",
            "dropoff_label": "Plateau",
            "service_tier": "standard",
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "MOBILITY_IDEMPOTENCY_REQUIRED"
    assert payload["message"]
    assert isinstance(payload["details"], dict)
    assert payload["correlation_id"]
