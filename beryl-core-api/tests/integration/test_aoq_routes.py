"""Integration-style tests for AOQ routes."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.orchestration.aoq.service import AoqNotFoundError, AoqValidationError


@pytest.mark.asyncio
async def test_create_signal_returns_201(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    signal_id = uuid4()
    fake_signal = SimpleNamespace(
        id=signal_id,
        user_id="user-1",
        source="mobile",
        created_at=datetime.now(timezone.utc),
    )

    class FakeService:
        def create_signal(self, user_id, source, payload):
            assert user_id == "user-1"
            assert source == "mobile"
            assert "features" in payload
            return fake_signal

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.post(
        "/api/v1/aoq/signals",
        headers={"Authorization": valid_tokens["social"]},
        json={
            "user_id": "user-1",
            "source": "mobile",
            "features": {
                "fintech_score": 80,
                "mobility_score": 70,
                "esg_score": 60,
                "social_score": 90,
            },
            "metadata": {"device": "android"},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["signal_id"] == str(signal_id)
    assert payload["user_id"] == "user-1"
    assert payload["source"] == "mobile"


@pytest.mark.asyncio
async def test_create_decision_returns_200(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    decision_id = uuid4()
    signal_id = uuid4()
    rule_id = uuid4()

    fake_decision = SimpleNamespace(
        decision_id=decision_id,
        signal_id=signal_id,
        rule_id=rule_id,
        user_id="user-1",
        score=72.5,
        threshold=60.0,
        decision="APPROVE",
        rationale="score=72.5 threshold=60",
        created_at=datetime.now(timezone.utc),
    )

    class FakeService:
        def compute_decision(self, user_id, signal_id, features_payload, metadata):
            assert user_id == "user-1"
            assert signal_id is None
            assert features_payload["fintech_score"] == 80
            return fake_decision

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.post(
        "/api/v1/aoq/decision",
        headers={"Authorization": valid_tokens["social"]},
        json={
            "user_id": "user-1",
            "features": {
                "fintech_score": 80,
                "mobility_score": 70,
                "esg_score": 60,
                "social_score": 90,
            },
            "metadata": {"flow": "checkout"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_id"] == str(decision_id)
    assert payload["decision"] == "APPROVE"


@pytest.mark.asyncio
async def test_get_and_create_rules(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    rule_id = uuid4()
    now = datetime.now(timezone.utc)
    fake_rule = SimpleNamespace(
        id=rule_id,
        name="default",
        threshold=60.0,
        weight_fintech=0.35,
        weight_mobility=0.25,
        weight_esg=0.25,
        weight_social=0.15,
        active=True,
        version=1,
        created_at=now,
        updated_at=now,
    )

    class FakeService:
        def list_rules(self):
            return [fake_rule]

        def create_rule(self, payload):
            assert payload["name"] == "risk-v2"
            return SimpleNamespace(**{**fake_rule.__dict__, "name": "risk-v2", "version": 2})

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    list_response = await async_client.get(
        "/api/v1/aoq/rules",
        headers={"Authorization": valid_tokens["social"]},
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "default"

    create_response = await async_client.post(
        "/api/v1/aoq/rules",
        headers={"Authorization": valid_tokens["social"]},
        json={
            "name": "risk-v2",
            "threshold": 62,
            "weight_fintech": 0.4,
            "weight_mobility": 0.2,
            "weight_esg": 0.2,
            "weight_social": 0.2,
            "active": True,
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "risk-v2"


@pytest.mark.asyncio
async def test_get_decision_by_id(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    decision_id = uuid4()
    signal_id = uuid4()
    rule_id = uuid4()

    fake_decision = SimpleNamespace(
        id=decision_id,
        signal_id=signal_id,
        rule_id=rule_id,
        user_id="user-9",
        score=40.0,
        threshold=60.0,
        decision="REJECT",
        rationale="score too low",
        created_at=datetime.now(timezone.utc),
    )

    class FakeService:
        def get_decision(self, incoming_decision_id):
            assert incoming_decision_id == decision_id
            return fake_decision

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.get(
        f"/api/v1/aoq/decisions/{decision_id}",
        headers={"Authorization": valid_tokens["social"]},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "REJECT"


@pytest.mark.asyncio
async def test_create_decision_validation_error_maps_to_400(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    class FakeService:
        def compute_decision(self, user_id, signal_id, features_payload, metadata):
            raise AoqValidationError("bad payload")

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.post(
        "/api/v1/aoq/decision",
        headers={"Authorization": valid_tokens["social"]},
        json={
            "user_id": "user-1",
            "features": {
                "fintech_score": 80,
                "mobility_score": 70,
                "esg_score": 60,
                "social_score": 90,
            },
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_decision_not_found_maps_to_404(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    class FakeService:
        def get_decision(self, decision_id):
            raise AoqNotFoundError("not found")

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.get(
        f"/api/v1/aoq/decisions/{uuid4()}",
        headers={"Authorization": valid_tokens["social"]},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_audit_trail(async_client, valid_tokens, monkeypatch):
    import src.api.v1.routes.aoq_routes as aoq_routes

    audit_entry = SimpleNamespace(
        id=uuid4(),
        event_type="AOQ_DECISION_CREATED",
        entity_id="dec-1",
        payload={"decision": "APPROVE"},
        signature="abc123",
        created_at=datetime.now(timezone.utc),
    )

    class FakeService:
        def get_audit_trail(self, entity_id):
            assert entity_id == "dec-1"
            return [audit_entry]

    monkeypatch.setattr(aoq_routes, "service", FakeService())

    response = await async_client.get(
        "/api/v1/aoq/audit/dec-1",
        headers={"Authorization": valid_tokens["social"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["entity_id"] == "dec-1"
    assert payload[0]["event_type"] == "AOQ_DECISION_CREATED"
