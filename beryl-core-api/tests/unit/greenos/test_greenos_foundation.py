"""Lot 1 foundation tests for GreenOS ESG v2."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from dataclasses import dataclass
from threading import Lock
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import HTTPException
from jose import jwt
from starlette.requests import Request
from sqlalchemy import delete, func, select, update

from src.config.settings import settings
from src.db.models.esg_greenos import (
    EsgAuditMetadataModel,
    EsgImpactLedgerModel,
    EsgMrvExportModel,
    EsgMrvMethodologyModel,
    EsgOutboxEventModel,
)
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.orchestration.esg.greenos.contracts.kafka import (
    TOPIC_ESG_CALCULATED_V1,
    TOPIC_GREENOS_DLQ_V1,
)
from src.orchestration.esg.greenos.iaesg import (
    AOQ_STATUS_PASS,
    AOQ_STATUS_REJECT,
    AOQ_STATUS_REVIEW,
    compute_confidence_score,
    compute_integrity_index,
    detect_anomalies,
    evaluate_aoq,
)
from src.orchestration.esg.greenos.ledger.repository import ImpactLedgerInsert, ImpactLedgerRepository
from src.orchestration.esg.greenos.mrv.engine import MrvExportEngine, MrvMethodologySnapshot
from src.orchestration.esg.greenos.mrv.methodology_repository import MrvMethodologyInsert, MrvMethodologyRepository
from src.orchestration.esg.greenos.outbox.relay_service import OutboxRelayService
from src.orchestration.esg.greenos.outbox.repository import GreenOSOutboxRepository
from src.orchestration.esg.greenos.schemas.requests import MrvExportQuery
from src.orchestration.esg.greenos.realtime.engine import CountryFactorSet, RealtimeImpactEngine
from src.orchestration.esg.greenos.schemas.requests import RealtimeCalculateRequest
from src.orchestration.esg.greenos.services.errors import (
    CountryFactorNotConfiguredError,
    MrvExportAlreadyExistsError,
    MrvMethodologyConflictError,
    MrvMethodologyValidationError,
)
from src.orchestration.esg.greenos.services.greenos_service import GreenOSService
from src.orchestration.esg.greenos.mrv.canonical import sha256_hex_strict
from src.orchestration.esg.greenos.services.signing import (
    SIGNATURE_ALGORITHM_ED25519,
    SIGNATURE_ALGORITHM_HMAC_SHA256,
    GreenOSSignatureService,
)
from src.orchestration.esg.greenos.secrets import (
    SECRET_GREENOS_SIGNING_SECRET,
    EnvSecretProvider,
    SecretMissingError,
    SecretProvider,
    VaultSecretProvider,
)


def _secure_headers(authorization: str) -> dict[str, str]:
    return {
        "Authorization": authorization,
        "X-Correlation-ID": str(uuid4()),
        "X-Nonce": str(uuid4()),
        "X-Timestamp": str(int(time.time())),
    }


def _generate_ed25519_keypair_b64() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.b64encode(private_bytes).decode("ascii"),
        base64.b64encode(public_bytes).decode("ascii"),
    )


def _create_active_mrv_methodology(
    *,
    methodology_version: str = "MRV-2026.1",
    baseline_description: str = "Baseline thermal mobility without EV substitution.",
    emission_factor_source: str = "GREENOS_COUNTRY_FACTORS_JSON",
    thermal_factor_reference: str = "IPCC thermal factor catalogue 2026",
    ev_factor_reference: str = "National EV grid factors 2026",
    calculation_formula: str = "distance_km * (thermal_factor_local - ev_factor_local)",
    geographic_scope: str = "CI,SN,KE",
) -> EsgMrvMethodologyModel:
    repository = MrvMethodologyRepository()
    return repository.create(
        MrvMethodologyInsert(
            methodology_version=methodology_version,
            baseline_description=baseline_description,
            emission_factor_source=emission_factor_source,
            thermal_factor_reference=thermal_factor_reference,
            ev_factor_reference=ev_factor_reference,
            calculation_formula=calculation_formula,
            geographic_scope=geographic_scope,
            model_version="greenos-co2-v1",
            status="ACTIVE",
        )
    )


@pytest.fixture
def mock_auth_upsert(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.api.v1.middlewares.auth_middleware._upsert_user",
        lambda firebase_uid, email, phone: "test-user-id",
    )


@pytest.fixture(autouse=True)
def clean_greenos_tables() -> None:
    """Ensure test isolation for append-only GreenOS tables."""
    Base.metadata.create_all(
        bind=get_engine(),
        tables=[
            EsgImpactLedgerModel.__table__,
            EsgAuditMetadataModel.__table__,
            EsgOutboxEventModel.__table__,
            EsgMrvExportModel.__table__,
            EsgMrvMethodologyModel.__table__,
        ],
        checkfirst=True,
    )
    session_factory = get_session_local()
    with session_factory() as session:
        session.execute(delete(EsgMrvExportModel))
        session.execute(delete(EsgMrvMethodologyModel))
        session.execute(delete(EsgOutboxEventModel))
        session.execute(delete(EsgAuditMetadataModel))
        session.execute(delete(EsgImpactLedgerModel))
        session.commit()


def test_co2_formula_correctness() -> None:
    engine = RealtimeImpactEngine(
        country_factors={"CI": CountryFactorSet(thermal_factor_local=0.2, ev_factor_local=0.05)},
        default_model_version="greenos-co2-v1",
    )
    request = RealtimeCalculateRequest(
        trip_id="trip-1",
        user_id="user-1",
        vehicle_id="veh-1",
        country_code="CI",
        distance_km=10.0,
        geo_hash="u0xj",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )
    result = engine.calculate(request)
    assert result.co2_avoided_kg == 1.5


def test_hash_is_stable_for_same_input() -> None:
    engine = RealtimeImpactEngine(
        country_factors={"CI": CountryFactorSet(thermal_factor_local=0.2, ev_factor_local=0.05)},
        default_model_version="greenos-co2-v1",
    )
    request = RealtimeCalculateRequest(
        trip_id="trip-hash",
        user_id="user-hash",
        vehicle_id="veh-hash",
        country_code="CI",
        distance_km=7.5,
        geo_hash="u0xj8",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )
    result_a = engine.calculate(request)
    result_b = engine.calculate(request)
    assert result_a.event_hash == result_b.event_hash
    assert result_a.checksum == result_b.checksum
    assert result_a.signature == result_b.signature
    assert result_a.signature_algorithm == SIGNATURE_ALGORITHM_HMAC_SHA256
    assert result_b.signature_algorithm == SIGNATURE_ALGORITHM_HMAC_SHA256
    assert result_a.key_version == result_b.key_version


def test_hmac_signature_stable_for_same_hash() -> None:
    service = GreenOSSignatureService(
        active_key_version="v1",
        active_secret="secret-v1",
        keyring={"v1": "secret-v1"},
    )
    first = service.sign_hash("a" * 64)
    second = service.sign_hash("a" * 64)
    assert first.signature == second.signature
    assert first.signature_algorithm == SIGNATURE_ALGORITHM_HMAC_SHA256
    assert first.key_version == "v1"


def test_ed25519_signature_is_valid_with_public_key_only() -> None:
    private_key_b64, public_key_b64 = _generate_ed25519_keypair_b64()
    service = GreenOSSignatureService(
        asym_active_key_version="v1",
        asym_private_key=private_key_b64,
        asym_public_key=public_key_b64,
        asym_private_keyring={"v1": private_key_b64},
        asym_public_keyring={"v1": public_key_b64},
    )
    signed = service.sign_hash_asymmetric("a" * 64)
    assert signed.signature_algorithm == SIGNATURE_ALGORITHM_ED25519
    assert signed.key_version == "v1"
    assert (
        GreenOSSignatureService.verify_hash_with_public_key(
            hash_value="a" * 64,
            signature=signed.signature,
            public_key=public_key_b64,
        )
        is True
    )


def test_signing_service_fails_closed_in_production_when_ed25519_missing(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "greenos_signing_secret", "prod-hmac-secret")
    with pytest.raises(
        RuntimeError,
        match=r"Ed25519 private key (is missing|placeholder cannot be used)",
    ):
        GreenOSSignatureService(
            asym_active_key_version="v1",
            asym_private_key="",
            asym_public_key="",
            asym_private_keyring={},
            asym_public_keyring={},
        )


def test_signature_rotation_multi_key_verification() -> None:
    signer = GreenOSSignatureService(
        active_key_version="v1",
        active_secret="secret-v1",
        keyring={"v1": "secret-v1"},
    )
    signed = signer.sign_hash("b" * 64)

    verifier = GreenOSSignatureService(
        active_key_version="v2",
        active_secret="secret-v2",
        keyring={"v1": "secret-v1", "v2": "secret-v2"},
    )
    assert (
        verifier.verify_hash_signature(
            hash_value="b" * 64,
            signature=signed.signature,
            signature_algorithm=signed.signature_algorithm,
            key_version=signed.key_version,
        )
        is True
    )


def test_env_secret_provider_resolves_runtime_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "greenos_signing_secret", "runtime-hmac-secret")
    provider = EnvSecretProvider(cache_ttl_seconds=0.0)
    assert provider.get_secret(SECRET_GREENOS_SIGNING_SECRET) == "runtime-hmac-secret"


def test_vault_secret_provider_reads_bundle_with_mock() -> None:
    class _MockVaultProvider(VaultSecretProvider):
        def __init__(self) -> None:
            super().__init__(
                vault_addr="http://vault.example.test",
                vault_token="token",
                vault_path="secret/data/greenos",
                cache_ttl_seconds=30.0,
            )
            self.fetch_calls = 0

        def _fetch_secret_bundle(self) -> dict[str, object]:
            self.fetch_calls += 1
            return {
                SECRET_GREENOS_SIGNING_SECRET: "vault-hmac-secret",
                "GREENOS_SIGNING_KEYS_JSON": {"v1": "vault-hmac-secret"},
            }

    provider = _MockVaultProvider()
    assert provider.get_secret(SECRET_GREENOS_SIGNING_SECRET) == "vault-hmac-secret"
    assert provider.get_json("GREENOS_SIGNING_KEYS_JSON") == {"v1": "vault-hmac-secret"}


def test_vault_secret_provider_cache_ttl_reuses_single_fetch() -> None:
    class _MockVaultProvider(VaultSecretProvider):
        def __init__(self) -> None:
            super().__init__(
                vault_addr="http://vault.example.test",
                vault_token="token",
                vault_path="secret/data/greenos",
                cache_ttl_seconds=60.0,
            )
            self.fetch_calls = 0

        def _fetch_secret_bundle(self) -> dict[str, object]:
            self.fetch_calls += 1
            return {SECRET_GREENOS_SIGNING_SECRET: "vault-cache-secret"}

    provider = _MockVaultProvider()
    assert provider.get_secret(SECRET_GREENOS_SIGNING_SECRET) == "vault-cache-secret"
    assert provider.get_secret(SECRET_GREENOS_SIGNING_SECRET) == "vault-cache-secret"
    assert provider.fetch_calls == 1


def test_signing_service_fails_closed_in_production_when_vault_secret_missing(monkeypatch) -> None:
    class _MissingVaultProvider(SecretProvider):
        provider_name = "vault"

        def __init__(self) -> None:
            super().__init__(cache_ttl_seconds=0.0)

        def _get_secret(self, *, name: str) -> str:
            raise SecretMissingError(f"missing secret {name}")

    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(RuntimeError, match="secret provider 'vault' is not ready"):
        GreenOSSignatureService(secret_provider=_MissingVaultProvider())


def test_iaesg_normal_case_score_is_high() -> None:
    features = {
        "distance_plausible": True,
        "country_factor_consistency": True,
        "timestamp_coherence": True,
        "timestamp_order_consistent": True,
        "country_supported": True,
        "methodology_consistency": True,
        "inferred_speed_kmh": 45.0,
        "burst_detected": False,
        "pattern_duplication": False,
        "historical_distance_deviation_ratio": 0.2,
        "crypto_integrity_ok": True,
    }
    score = compute_confidence_score(features)
    integrity = compute_integrity_index(features)
    flags = detect_anomalies(features)

    assert score >= 80
    assert integrity >= 70
    assert flags == []
    assert evaluate_aoq(score, flags) == AOQ_STATUS_PASS


def test_iaesg_distance_implausible_degrades_score_and_flags() -> None:
    features = {
        "distance_plausible": False,
        "country_factor_consistency": True,
        "timestamp_coherence": True,
        "timestamp_order_consistent": True,
        "country_supported": True,
        "methodology_consistency": True,
        "inferred_speed_kmh": 90.0,
        "burst_detected": False,
        "pattern_duplication": False,
        "historical_distance_deviation_ratio": 0.2,
        "crypto_integrity_ok": True,
    }
    score = compute_confidence_score(features)
    flags = detect_anomalies(features)

    assert score <= 50
    assert "DISTANCE_IMPLAUSIBLE" in flags


def test_iaesg_speed_out_of_range_flagged() -> None:
    features = {
        "distance_plausible": True,
        "country_factor_consistency": True,
        "timestamp_coherence": True,
        "timestamp_order_consistent": True,
        "country_supported": True,
        "methodology_consistency": True,
        "inferred_speed_kmh": 280.0,
        "burst_detected": False,
        "pattern_duplication": False,
        "historical_distance_deviation_ratio": 0.3,
        "crypto_integrity_ok": True,
    }
    flags = detect_anomalies(features)
    assert "SPEED_OUT_OF_RANGE" in flags


def test_iaesg_pattern_duplication_lowers_confidence() -> None:
    features = {
        "distance_plausible": True,
        "country_factor_consistency": True,
        "timestamp_coherence": True,
        "timestamp_order_consistent": True,
        "country_supported": True,
        "methodology_consistency": True,
        "inferred_speed_kmh": 80.0,
        "burst_detected": True,
        "pattern_duplication": True,
        "historical_distance_deviation_ratio": 0.2,
        "crypto_integrity_ok": True,
    }
    score = compute_confidence_score(features)
    flags = detect_anomalies(features)
    aoq_status = evaluate_aoq(score, flags)

    assert score <= 60
    assert "PATTERN_DUPLICATION" in flags
    assert aoq_status in {AOQ_STATUS_REVIEW, AOQ_STATUS_REJECT}


def test_iaesg_methodology_inconsistence_rejects() -> None:
    features = {
        "distance_plausible": True,
        "country_factor_consistency": False,
        "timestamp_coherence": True,
        "timestamp_order_consistent": True,
        "country_supported": False,
        "methodology_consistency": False,
        "inferred_speed_kmh": 60.0,
        "burst_detected": False,
        "pattern_duplication": False,
        "historical_distance_deviation_ratio": 0.2,
        "crypto_integrity_ok": True,
    }
    score = compute_confidence_score(features)
    flags = detect_anomalies(features)
    assert "METHODOLOGY_INCONSISTENCE" in flags
    assert evaluate_aoq(score, flags) == AOQ_STATUS_REJECT


def test_iaesg_crypto_integrity_failure_rejects() -> None:
    features = {
        "distance_plausible": True,
        "country_factor_consistency": True,
        "timestamp_coherence": True,
        "timestamp_order_consistent": True,
        "country_supported": True,
        "methodology_consistency": True,
        "inferred_speed_kmh": 50.0,
        "burst_detected": False,
        "pattern_duplication": False,
        "historical_distance_deviation_ratio": 0.1,
        "crypto_integrity_ok": False,
    }
    score = compute_confidence_score(features)
    flags = detect_anomalies(features)

    assert score < 50
    assert "CRYPTO_INTEGRITY_FAILURE" in flags
    assert evaluate_aoq(score, flags) == AOQ_STATUS_REJECT


def test_iaesg_aoq_status_mapping_pass_review_reject() -> None:
    assert evaluate_aoq(90, []) == AOQ_STATUS_PASS
    assert evaluate_aoq(65, []) == AOQ_STATUS_REVIEW
    assert evaluate_aoq(45, []) == AOQ_STATUS_REJECT
    assert evaluate_aoq(85, ["CRYPTO_INTEGRITY_FAILURE"]) == AOQ_STATUS_REJECT


def test_iaesg_realtime_computation_is_deterministic() -> None:
    engine = RealtimeImpactEngine(
        country_factors={"CI": CountryFactorSet(thermal_factor_local=0.2, ev_factor_local=0.05)},
        default_model_version="greenos-co2-v1",
    )
    request = RealtimeCalculateRequest(
        trip_id="trip-iaesg-deterministic",
        user_id="user-iaesg-deterministic",
        vehicle_id="veh-iaesg-deterministic",
        country_code="CI",
        distance_km=12.4,
        geo_hash="u0xid1",
        model_version="greenos-co2-v1",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )
    history = [
        {
            "distance_km": 9.0,
            "country_code": "CI",
            "geo_hash": "u0xid1",
            "event_timestamp": datetime(2026, 2, 13, 9, 0, 0, tzinfo=UTC),
        }
    ]
    first = engine.calculate(request, history=history)
    second = engine.calculate(request, history=history)

    assert first.confidence_score == second.confidence_score
    assert first.integrity_index == second.integrity_index
    assert first.anomaly_flags == second.anomaly_flags
    assert first.aoq_status == second.aoq_status
    assert first.explanation == second.explanation


@pytest.mark.asyncio
async def test_mrv_export_payload_and_hash_are_stable() -> None:
    service = GreenOSService()
    methodology = _create_active_mrv_methodology()
    reference_time = datetime(2026, 2, 17, 12, 0, 0, tzinfo=UTC)
    event_time = reference_time - timedelta(days=1)
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-stable",
            user_id="user-mrv-stable",
            vehicle_id="veh-mrv-stable",
            country_code="CI",
            distance_km=11.2,
            geo_hash="u0xms",
            model_version="greenos-co2-v1",
            event_timestamp=event_time,
        ),
        correlation_id="corr-mrv-stable",
    )

    signature_service = GreenOSSignatureService(
        active_key_version="v1",
        active_secret="secret-v1",
        keyring={"v1": "secret-v1"},
    )
    engine = MrvExportEngine(
        ledger_repository=ImpactLedgerRepository(),
        signature_service=signature_service,
    )
    snapshot = MrvMethodologySnapshot(
        methodology_version=methodology.methodology_version,
        baseline_description=methodology.baseline_description,
        emission_factor_source=methodology.emission_factor_source,
        thermal_factor_reference=methodology.thermal_factor_reference,
        ev_factor_reference=methodology.ev_factor_reference,
        calculation_formula=methodology.calculation_formula,
        geographic_scope=methodology.geographic_scope,
        model_version=methodology.model_version,
    )
    first = engine.build_export(period="3M", methodology=snapshot, reference_time=reference_time)
    second = engine.build_export(period="3M", methodology=snapshot, reference_time=reference_time)

    assert first.payload == second.payload
    assert first.verification_hash == second.verification_hash
    assert first.signature == second.signature
    assert first.verification_hash == sha256_hex_strict(first.payload)


@pytest.mark.asyncio
async def test_mrv_export_blocks_double_counting_on_same_trip() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology()
    event_time = datetime.now(UTC) - timedelta(days=1)
    trip_id = "trip-mrv-dedup"
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-mrv-dedup",
            vehicle_id="veh-mrv-dedup",
            country_code="CI",
            distance_km=7.4,
            geo_hash="u0xmd",
            model_version="greenos-co2-v1",
            event_timestamp=event_time,
        ),
        correlation_id="corr-mrv-dedup-v1",
    )
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-mrv-dedup",
            vehicle_id="veh-mrv-dedup",
            country_code="CI",
            distance_km=7.4,
            geo_hash="u0xmd",
            model_version="greenos-co2-v2",
            event_timestamp=event_time + timedelta(minutes=1),
        ),
        correlation_id="corr-mrv-dedup-v2",
    )

    export_record = service.export_mrv_report(period="3M", correlation_id="corr-mrv-export-dedup")
    proof = export_record.payload.get("non_double_counting_proof", {})
    aggregation = export_record.payload.get("aggregation", {})
    assert isinstance(proof, dict)
    assert isinstance(aggregation, dict)
    assert proof.get("duplicates_removed_count") == 1
    assert aggregation.get("impacts_count") == 1


@pytest.mark.asyncio
async def test_mrv_export_rejects_duplicate_period() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-duplicate-period",
            user_id="user-mrv-duplicate-period",
            vehicle_id="veh-mrv-duplicate-period",
            country_code="CI",
            distance_km=9.3,
            geo_hash="u0xmp",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-mrv-duplicate-period",
    )

    service.export_mrv_report(period="3M", correlation_id="corr-mrv-export-1")
    with pytest.raises(MrvExportAlreadyExistsError):
        service.export_mrv_report(period="3M", correlation_id="corr-mrv-export-2")


def test_mrv_methodology_enforces_single_active_version() -> None:
    _create_active_mrv_methodology(methodology_version="MRV-2026.1")
    with pytest.raises(MrvMethodologyConflictError):
        _create_active_mrv_methodology(methodology_version="MRV-2026.2")


def test_mrv_methodology_lookup_current_and_version() -> None:
    methodology = _create_active_mrv_methodology(methodology_version="MRV-2026.1")
    service = GreenOSService()
    current = service.get_current_mrv_methodology()
    by_version = service.get_mrv_methodology_by_version(version="MRV-2026.1")
    assert current.id == methodology.id
    assert by_version.id == methodology.id


def test_mrv_export_requires_documented_baseline() -> None:
    _create_active_mrv_methodology(baseline_description="   ")
    service = GreenOSService()
    with pytest.raises(MrvMethodologyValidationError):
        service.export_mrv_report(period="3M", correlation_id="corr-mrv-baseline-missing")


def test_mrv_export_requires_documented_country_factors(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "greenos_country_factors_json",
        json.dumps(
            {
                "CI": {
                    "thermal_factor_local": 0.2,
                    "ev_factor_local": 0.05,
                }
            }
        ),
    )
    _create_active_mrv_methodology(geographic_scope="CI,SN")
    service = GreenOSService()
    with pytest.raises(MrvMethodologyValidationError):
        service.export_mrv_report(period="3M", correlation_id="corr-mrv-country-factors-missing")


@pytest.mark.asyncio
async def test_mrv_export_is_linked_to_active_methodology() -> None:
    methodology = _create_active_mrv_methodology(methodology_version="MRV-2026.1")
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-method-link",
            user_id="user-mrv-method-link",
            vehicle_id="veh-mrv-method-link",
            country_code="CI",
            distance_km=6.4,
            geo_hash="u0xml",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-mrv-method-link",
    )

    record = service.export_mrv_report(period="3M", correlation_id="corr-mrv-method-link-export")
    assert record.methodology_id == methodology.id
    assert record.methodology_version == methodology.methodology_version
    assert bool(record.methodology_hash)

    verification = service.verify_mrv_export(export_id=str(record.id))
    assert verification["methodology_valid"] is True
    assert verification["verified"] is True


@pytest.mark.asyncio
async def test_mrv_hash_changes_when_methodology_changes() -> None:
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-method-diff",
            user_id="user-mrv-method-diff",
            vehicle_id="veh-mrv-method-diff",
            country_code="CI",
            distance_km=10.1,
            geo_hash="u0xmh",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 16, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-mrv-method-diff",
    )

    reference_time = datetime(2026, 2, 17, 12, 0, 0, tzinfo=UTC)
    signature_service = GreenOSSignatureService(
        active_key_version="v1",
        active_secret="secret-v1",
        keyring={"v1": "secret-v1"},
    )
    engine = MrvExportEngine(
        ledger_repository=ImpactLedgerRepository(),
        signature_service=signature_service,
    )
    methodology_v1 = MrvMethodologySnapshot(
        methodology_version="MRV-2026.1",
        baseline_description="Baseline thermal mobility without EV substitution.",
        emission_factor_source="GREENOS_COUNTRY_FACTORS_JSON",
        thermal_factor_reference="IPCC thermal factor catalogue 2026",
        ev_factor_reference="National EV grid factors 2026",
        calculation_formula="distance_km * (thermal_factor_local - ev_factor_local)",
        geographic_scope="CI,SN,KE",
        model_version="greenos-co2-v1",
    )
    methodology_v2 = MrvMethodologySnapshot(
        methodology_version="MRV-2026.2",
        baseline_description="Updated baseline for urban EV adoption.",
        emission_factor_source="GREENOS_COUNTRY_FACTORS_JSON",
        thermal_factor_reference="IPCC thermal factor catalogue 2026",
        ev_factor_reference="National EV grid factors 2026",
        calculation_formula="distance_km * (thermal_factor_local - ev_factor_local) * 0.99",
        geographic_scope="CI,SN,KE",
        model_version="greenos-co2-v1",
    )
    export_v1 = engine.build_export(period="3M", methodology=methodology_v1, reference_time=reference_time)
    export_v2 = engine.build_export(period="3M", methodology=methodology_v2, reference_time=reference_time)

    assert export_v1.methodology_hash != export_v2.methodology_hash
    assert export_v1.verification_hash != export_v2.verification_hash


def test_absence_of_fallback_when_country_not_configured() -> None:
    engine = RealtimeImpactEngine(
        country_factors={"CI": CountryFactorSet(thermal_factor_local=0.2, ev_factor_local=0.05)},
        default_model_version="greenos-co2-v1",
    )
    request = RealtimeCalculateRequest(
        trip_id="trip-no-country",
        user_id="user-no-country",
        vehicle_id="veh-no-country",
        country_code="GH",
        distance_km=3.0,
        geo_hash="u0xj9",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )
    with pytest.raises(CountryFactorNotConfiguredError):
        engine.calculate(request)


def test_idempotency_and_non_double_insertion_on_ledger() -> None:
    repository = ImpactLedgerRepository()
    payload = ImpactLedgerInsert(
        trip_id="trip-idempotent",
        user_id="user-idempotent",
        vehicle_id="veh-idempotent",
        country_code="CI",
        geo_hash="u0xja",
        distance_km=9.8,
        co2_avoided_kg=1.1,
        thermal_factor_local=0.2,
        ev_factor_local=0.05,
        model_version="greenos-co2-v1",
        event_hash="abc123" * 10,
        checksum="def456" * 10,
        signature="789abc" * 10,
        signature_algorithm="HMAC-SHA256",
        key_version="v1",
        asym_signature="a" * 88,
        asym_algorithm="ED25519",
        asym_key_version="v1",
        correlation_id="corr-idempotent",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )

    first_record, first_idempotent = repository.create_or_get(payload)
    second_record, second_idempotent = repository.create_or_get(payload)

    assert first_idempotent is False
    assert second_idempotent is True
    assert first_record.id == second_record.id

    session_factory = get_session_local()
    with session_factory() as session:
        count = session.execute(select(func.count()).select_from(EsgImpactLedgerModel)).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_ledger_and_outbox_insert_are_atomic() -> None:
    class FailingOutboxRepository:
        @staticmethod
        def enqueue(*, session, payload):
            raise RuntimeError("forced outbox failure")

    service = GreenOSService(outbox_repository=FailingOutboxRepository())
    trip_id = f"trip-atomic-fail-{uuid4().hex}"
    correlation_id = f"corr-atomic-fail-{uuid4().hex}"

    with pytest.raises(RuntimeError, match="forced outbox failure"):
        await service.calculate_realtime_impact(
            request=RealtimeCalculateRequest(
                trip_id=trip_id,
                user_id="user-atomic-fail",
                vehicle_id="veh-atomic-fail",
                country_code="CI",
                distance_km=8.5,
                geo_hash="u0xzz",
                model_version="greenos-co2-v1",
                event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
            ),
            correlation_id=correlation_id,
        )

    session_factory = get_session_local()
    with session_factory() as session:
        ledger_count = session.execute(
            select(func.count())
            .select_from(EsgImpactLedgerModel)
            .where(EsgImpactLedgerModel.trip_id == trip_id)
        ).scalar_one()
        outbox_rows = session.execute(select(EsgOutboxEventModel)).scalars().all()
        outbox_count = sum(
            1
            for row in outbox_rows
            if isinstance(row.payload, dict) and row.payload.get("correlation_id") == correlation_id
        )
    assert ledger_count == 0
    assert outbox_count == 0


@pytest.mark.asyncio
async def test_outbox_relay_retries_then_marks_sent() -> None:
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-retry-1",
            user_id="user-retry-1",
            vehicle_id="veh-retry-1",
            country_code="CI",
            distance_km=6.2,
            geo_hash="u0xre",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-retry-1",
    )

    class FlakyPublisher:
        def __init__(self) -> None:
            self.calls = 0

        async def publish(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("kafka down")
            return {"event_id": kwargs.get("event_id")}

    flaky = FlakyPublisher()
    relay = OutboxRelayService(
        repository=GreenOSOutboxRepository(),
        publisher=flaky,
        max_retry_count=3,
        base_retry_seconds=0.0,
    )

    first_run = await relay.run_once(limit=10)
    assert first_run["retried"] == 1
    assert first_run["published"] == 0

    second_run = await relay.run_once(limit=10)
    assert second_run["published"] == 1
    assert flaky.calls == 2

    session_factory = get_session_local()
    with session_factory() as session:
        row = session.execute(select(EsgOutboxEventModel)).scalar_one()
        assert row.status == "SENT"
        assert row.retry_count == 1


@pytest.mark.asyncio
async def test_outbox_relay_publishes_dlq_and_marks_failed() -> None:
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-dlq-1",
            user_id="user-dlq-1",
            vehicle_id="veh-dlq-1",
            country_code="CI",
            distance_km=4.4,
            geo_hash="u0xdlq",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-dlq-1",
    )

    class AlwaysFailWithDlqPublisher:
        def __init__(self) -> None:
            self.dlq_calls: list[dict[str, object]] = []

        async def publish(self, **kwargs):
            raise RuntimeError("kafka down hard")

        async def publish_dlq(self, **kwargs):
            self.dlq_calls.append(kwargs)
            return {"event_id": kwargs.get("event_id")}

    publisher = AlwaysFailWithDlqPublisher()
    relay = OutboxRelayService(
        repository=GreenOSOutboxRepository(),
        publisher=publisher,
        max_retry_count=0,
        base_retry_seconds=0.0,
    )

    result = await relay.run_once(limit=10)
    assert result["failed"] == 1
    assert result["retried"] == 0
    assert len(publisher.dlq_calls) == 1

    dlq_payload = publisher.dlq_calls[0]["payload"]
    assert isinstance(dlq_payload, dict)
    assert dlq_payload["event_type"] == TOPIC_ESG_CALCULATED_V1
    assert dlq_payload["reason"] == "kafka down hard"

    session_factory = get_session_local()
    with session_factory() as session:
        row = session.execute(select(EsgOutboxEventModel)).scalar_one()
        assert row.status == "FAILED"
        assert row.retry_count == 1


@pytest.mark.asyncio
async def test_outbox_relay_marks_failed_after_retry_threshold() -> None:
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-retry-fail-1",
            user_id="user-retry-fail-1",
            vehicle_id="veh-retry-fail-1",
            country_code="CI",
            distance_km=3.4,
            geo_hash="u0xrf",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-retry-fail-1",
    )

    class AlwaysFailPublisher:
        async def publish(self, **kwargs):
            raise RuntimeError("kafka still down")

    relay = OutboxRelayService(
        repository=GreenOSOutboxRepository(),
        publisher=AlwaysFailPublisher(),
        max_retry_count=1,
        base_retry_seconds=0.0,
    )

    first_run = await relay.run_once(limit=10)
    assert first_run["retried"] == 1
    assert first_run["failed"] == 0

    second_run = await relay.run_once(limit=10)
    assert second_run["failed"] == 1

    session_factory = get_session_local()
    with session_factory() as session:
        row = session.execute(select(EsgOutboxEventModel)).scalar_one()
        assert row.status == "FAILED"
        assert row.retry_count == 2


@pytest.mark.asyncio
async def test_outbox_relay_multi_worker_safety_no_double_publish() -> None:
    @dataclass
    class _OutboxRow:
        id: str
        aggregate_type: str
        aggregate_id: str
        event_type: str
        payload: dict[str, object]
        status: str = "PENDING"
        retry_count: int = 0
        last_attempt_at: datetime | None = None

    class _Session:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        @staticmethod
        def commit() -> None:
            return None

    class SharedClaimRepository:
        def __init__(self, rows: list[_OutboxRow]) -> None:
            self._rows = rows
            self._claimed_ids: set[str] = set()
            self._lock = Lock()

        @property
        def session_factory(self):
            return _Session

        def claim_pending(self, *, session, limit: int):
            _ = session
            with self._lock:
                claimed = []
                for row in self._rows:
                    if row.status != "PENDING":
                        continue
                    if row.id in self._claimed_ids:
                        continue
                    self._claimed_ids.add(row.id)
                    claimed.append(row)
                    if len(claimed) >= limit:
                        break
                return claimed

        def count_pending(self, *, session) -> int:
            _ = session
            with self._lock:
                return sum(1 for row in self._rows if row.status == "PENDING")

        @staticmethod
        def mark_sent(*, row, attempted_at: datetime | None = None) -> None:
            row.status = "SENT"
            row.last_attempt_at = attempted_at or datetime.now(UTC)

        @staticmethod
        def mark_retry(*, row, attempted_at: datetime | None = None) -> None:
            row.retry_count += 1
            row.status = "PENDING"
            row.last_attempt_at = attempted_at or datetime.now(UTC)

        @staticmethod
        def mark_failed(*, row, attempted_at: datetime | None = None) -> None:
            row.retry_count += 1
            row.status = "FAILED"
            row.last_attempt_at = attempted_at or datetime.now(UTC)

    class SlowPublisher:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def publish(self, **kwargs):
            self.calls.append(str(kwargs.get("event_id")))
            await asyncio.sleep(0.01)
            return {"event_id": kwargs.get("event_id")}

        async def publish_dlq(self, **kwargs):
            _ = kwargs
            return {"ok": True}

    row = _OutboxRow(
        id=str(uuid4()),
        aggregate_type="esg_impact_ledger",
        aggregate_id=str(uuid4()),
        event_type=TOPIC_ESG_CALCULATED_V1,
        payload={
            "correlation_id": "corr-multi-worker",
            "event_payload": {
                "ledger_id": str(uuid4()),
                "trip_id": "trip-multi-worker",
                "user_id": "user-multi-worker",
                "country_code": "CI",
                "co2_avoided_kg": 1.0,
                "model_version": "greenos-co2-v1",
                "checksum": "a" * 64,
                "event_hash": "b" * 64,
                "signature": "c" * 64,
                "geo_hash": "u0xmw",
                "event_timestamp": "2026-02-13T10:00:00+00:00",
            },
        },
    )
    repo = SharedClaimRepository([row])
    publisher = SlowPublisher()
    relay_a = OutboxRelayService(repository=repo, publisher=publisher, max_retry_count=3, base_retry_seconds=0.0)
    relay_b = OutboxRelayService(repository=repo, publisher=publisher, max_retry_count=3, base_retry_seconds=0.0)

    result_a, result_b = await asyncio.gather(relay_a.run_once(limit=1), relay_b.run_once(limit=1))
    assert result_a["published"] + result_b["published"] == 1
    assert len(publisher.calls) == 1
    assert row.status == "SENT"


def test_outbox_claim_pending_uses_skip_locked_for_postgresql() -> None:
    class _FakeDialect:
        name = "postgresql"

    class _FakeBind:
        dialect = _FakeDialect()

    class _FakeResult:
        @staticmethod
        def scalars():
            return _FakeResult()

        @staticmethod
        def all():
            return []

    class _FakeSession:
        def __init__(self) -> None:
            self.captured_stmt = None

        @staticmethod
        def get_bind():
            return _FakeBind()

        def execute(self, stmt):
            self.captured_stmt = stmt
            return _FakeResult()

    repository = GreenOSOutboxRepository()
    session = _FakeSession()
    rows = repository.claim_pending(session=session, limit=10)
    assert rows == []
    assert session.captured_stmt is not None
    assert session.captured_stmt._for_update_arg is not None  # pylint: disable=protected-access
    assert session.captured_stmt._for_update_arg.skip_locked is True  # pylint: disable=protected-access


@pytest.mark.asyncio
async def test_idempotent_double_call_does_not_duplicate_outbox_event() -> None:
    service = GreenOSService()
    payload = RealtimeCalculateRequest(
        trip_id="trip-idem-outbox",
        user_id="user-idem-outbox",
        vehicle_id="veh-idem-outbox",
        country_code="CI",
        distance_km=5.0,
        geo_hash="u0xid",
        model_version="greenos-co2-v1",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )

    _, first_idempotent = await service.calculate_realtime_impact(
        request=payload,
        correlation_id="corr-idem-outbox-1",
    )
    _, second_idempotent = await service.calculate_realtime_impact(
        request=payload,
        correlation_id="corr-idem-outbox-2",
    )

    assert first_idempotent is False
    assert second_idempotent is True

    session_factory = get_session_local()
    with session_factory() as session:
        ledger_count = session.execute(select(func.count()).select_from(EsgImpactLedgerModel)).scalar_one()
        outbox_count = session.execute(select(func.count()).select_from(EsgOutboxEventModel)).scalar_one()
    assert ledger_count == 1
    assert outbox_count == 1


@pytest.mark.asyncio
async def test_audit_preview_generates_hash_and_persists_metadata() -> None:
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-audit-1",
            user_id="user-audit-1",
            vehicle_id="veh-audit-1",
            country_code="CI",
            distance_km=4.0,
            geo_hash="u0xb7",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-audit-1",
    )
    audit_record = await service.preview_audit(
        window="3M",
        correlation_id="corr-audit-2",
        country_code="CI",
    )
    assert audit_record.report_hash
    assert audit_record.trips_count >= 1


@pytest.mark.asyncio
async def test_invalid_payload_returns_422(async_client, valid_tokens, mock_auth_upsert) -> None:
    response = await async_client.post(
        "/api/v2/esg/realtime/calculate",
        headers=_secure_headers(valid_tokens["esg"]),
        json={
            "trip_id": "trip-422",
            "user_id": "user-422",
            "vehicle_id": "veh-422",
            "country_code": "CI",
            "distance_km": "10.5",
            "geo_hash": "u0xb3",
            "model_version": "greenos-co2-v1",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_country_without_factor_returns_explicit_error(async_client, valid_tokens, mock_auth_upsert) -> None:
    response = await async_client.post(
        "/api/v2/esg/realtime/calculate",
        headers=_secure_headers(valid_tokens["esg"]),
        json={
            "trip_id": "trip-factor-error",
            "user_id": "user-factor-error",
            "vehicle_id": "veh-factor-error",
            "country_code": "GH",
            "distance_km": 10.5,
            "geo_hash": "u0xb4",
            "model_version": "greenos-co2-v1",
        },
    )
    assert response.status_code == 400
    payload = response.json()
    error_code = payload.get("code") or payload.get("detail", {}).get("code")
    assert error_code == "GREENOS_COUNTRY_FACTOR_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_v2_realtime_and_get_impact_flow(async_client, valid_tokens, mock_auth_upsert) -> None:
    calculate_response = await async_client.post(
        "/api/v2/esg/realtime/calculate",
        headers=_secure_headers(valid_tokens["esg"]),
        json={
            "trip_id": "trip-flow-1",
            "user_id": "user-flow-1",
            "vehicle_id": "veh-flow-1",
            "country_code": "CI",
            "distance_km": 12.0,
            "geo_hash": "u0xb9",
            "model_version": "greenos-co2-v1",
        },
    )
    assert calculate_response.status_code == 200
    calculation_payload = calculate_response.json()
    assert calculation_payload["idempotent"] is False
    assert calculation_payload["co2_avoided_kg"] > 0

    impact_response = await async_client.get(
        "/api/v2/esg/impact/trip-flow-1",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert impact_response.status_code == 200
    impact_payload = impact_response.json()
    assert impact_payload["trip_id"] == "trip-flow-1"
    assert impact_payload["checksum"]


@pytest.mark.asyncio
async def test_v2_impact_confidence_endpoint_returns_iaesg_payload(async_client, valid_tokens, mock_auth_upsert) -> None:
    trip_id = "trip-confidence-endpoint"
    calculate_response = await async_client.post(
        "/api/v2/esg/realtime/calculate",
        headers=_secure_headers(valid_tokens["esg"]),
        json={
            "trip_id": trip_id,
            "user_id": "user-confidence-endpoint",
            "vehicle_id": "veh-confidence-endpoint",
            "country_code": "CI",
            "distance_km": 10.8,
            "geo_hash": "u0xcnf",
            "model_version": "greenos-co2-v1",
        },
    )
    assert calculate_response.status_code == 200

    confidence_response = await async_client.get(
        f"/api/v2/esg/impact/{trip_id}/confidence",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert confidence_response.status_code == 200
    payload = confidence_response.json()
    assert payload["trip_id"] == trip_id
    assert isinstance(payload["confidence_score"], int)
    assert isinstance(payload["integrity_index"], int)
    assert payload["aoq_status"] in {AOQ_STATUS_PASS, AOQ_STATUS_REVIEW, AOQ_STATUS_REJECT}
    assert isinstance(payload["anomaly_flags"], list)
    assert isinstance(payload["reasoning_summary"], dict)


@pytest.mark.asyncio
async def test_v2_mrv_confidence_summary_endpoint_returns_payload(async_client, valid_tokens, mock_auth_upsert) -> None:
    service = GreenOSService()
    _create_active_mrv_methodology(methodology_version="MRV-IAESG-ENDPOINT-2026.1")
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-confidence-endpoint",
            user_id="user-mrv-confidence-endpoint",
            vehicle_id="veh-mrv-confidence-endpoint",
            country_code="CI",
            distance_km=8.1,
            geo_hash="u0xmcs",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-mrv-confidence-endpoint",
    )
    export_record = service.export_mrv_report(period="3M", correlation_id="corr-mrv-confidence-endpoint-export")

    response = await async_client.get(
        f"/api/v2/esg/mrv/export/{export_record.id}/confidence-summary",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["export_id"] == str(export_record.id)
    assert isinstance(payload["average_confidence"], float)
    assert isinstance(payload["average_integrity"], float)
    assert isinstance(payload["anomaly_breakdown"], dict)
    assert payload["aoq_status"] in {AOQ_STATUS_PASS, AOQ_STATUS_REVIEW, AOQ_STATUS_REJECT}


@pytest.mark.asyncio
async def test_verify_endpoint_returns_400_when_signature_invalid(async_client, valid_tokens, mock_auth_upsert) -> None:
    trip_id = "trip-verify-signature-invalid"
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-verify-signature-invalid",
            vehicle_id="veh-verify-signature-invalid",
            country_code="CI",
            distance_km=8.0,
            geo_hash="u0xsv",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-verify-signature-invalid",
    )

    session_factory = get_session_local()
    with session_factory() as session:
        session.execute(
            update(EsgImpactLedgerModel)
            .where(EsgImpactLedgerModel.trip_id == trip_id)
            .values(signature="0" * 64)
        )
        session.commit()

    response = await async_client.get(
        f"/api/v2/esg/verify/{trip_id}",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert response.status_code == 400
    payload = response.json()
    error_code = payload.get("code") or payload.get("detail", {}).get("code")
    assert error_code == "GREENOS_INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_verify_endpoint_returns_400_when_asymmetric_signature_invalid(
    async_client,
    valid_tokens,
    mock_auth_upsert,
) -> None:
    trip_id = "trip-verify-asym-signature-invalid"
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-verify-asym-signature-invalid",
            vehicle_id="veh-verify-asym-signature-invalid",
            country_code="CI",
            distance_km=8.0,
            geo_hash="u0xsa",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-verify-asym-signature-invalid",
    )

    session_factory = get_session_local()
    with session_factory() as session:
        session.execute(
            update(EsgImpactLedgerModel)
            .where(EsgImpactLedgerModel.trip_id == trip_id)
            .values(asym_signature="invalid-base64-signature")
        )
        session.commit()

    response = await async_client.get(
        f"/api/v2/esg/verify/{trip_id}",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert response.status_code == 400
    payload = response.json()
    error_code = payload.get("code") or payload.get("detail", {}).get("code")
    assert error_code == "GREENOS_INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_verify_endpoint_detects_payload_tampering(async_client, valid_tokens, mock_auth_upsert) -> None:
    trip_id = "trip-verify-tamper"
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-verify-tamper",
            vehicle_id="veh-verify-tamper",
            country_code="CI",
            distance_km=8.3,
            geo_hash="u0xtm",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-verify-tamper",
    )

    session_factory = get_session_local()
    with session_factory() as session:
        session.execute(
            update(EsgImpactLedgerModel)
            .where(EsgImpactLedgerModel.trip_id == trip_id)
            .values(event_hash="f" * 64)
        )
        session.commit()

    response = await async_client.get(
        f"/api/v2/esg/verify/{trip_id}",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert response.status_code == 400
    payload = response.json()
    error_code = payload.get("code") or payload.get("detail", {}).get("code")
    assert error_code == "GREENOS_PAYLOAD_TAMPERED"


@pytest.mark.asyncio
async def test_verify_endpoint_supports_key_rotation(async_client, valid_tokens, mock_auth_upsert, monkeypatch) -> None:
    private_v1, public_v1 = _generate_ed25519_keypair_b64()
    private_v2, public_v2 = _generate_ed25519_keypair_b64()

    monkeypatch.setattr(settings, "greenos_signing_active_key_version", "v1")
    monkeypatch.setattr(settings, "greenos_signing_secret", "secret-v1")
    monkeypatch.setattr(settings, "greenos_signing_keys_json", json.dumps({"v1": "secret-v1"}))
    monkeypatch.setattr(settings, "greenos_ed25519_active_key_version", "v1")
    monkeypatch.setattr(settings, "greenos_ed25519_private_key", private_v1)
    monkeypatch.setattr(settings, "greenos_ed25519_public_key", public_v1)
    monkeypatch.setattr(settings, "greenos_ed25519_private_keys_json", json.dumps({"v1": private_v1}))
    monkeypatch.setattr(settings, "greenos_ed25519_public_keys_json", json.dumps({"v1": public_v1}))

    trip_id = "trip-verify-rotation"
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-verify-rotation",
            vehicle_id="veh-verify-rotation",
            country_code="CI",
            distance_km=9.1,
            geo_hash="u0xrt",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-verify-rotation",
    )

    monkeypatch.setattr(settings, "greenos_signing_active_key_version", "v2")
    monkeypatch.setattr(settings, "greenos_signing_secret", "secret-v2")
    monkeypatch.setattr(
        settings,
        "greenos_signing_keys_json",
        json.dumps({"v1": "secret-v1", "v2": "secret-v2"}),
    )
    monkeypatch.setattr(settings, "greenos_ed25519_active_key_version", "v2")
    monkeypatch.setattr(settings, "greenos_ed25519_private_key", private_v2)
    monkeypatch.setattr(settings, "greenos_ed25519_public_key", public_v2)
    monkeypatch.setattr(
        settings,
        "greenos_ed25519_private_keys_json",
        json.dumps({"v1": private_v1, "v2": private_v2}),
    )
    monkeypatch.setattr(
        settings,
        "greenos_ed25519_public_keys_json",
        json.dumps({"v1": public_v1, "v2": public_v2}),
    )

    response = await async_client.get(
        f"/api/v2/esg/verify/{trip_id}",
        headers={
            "Authorization": valid_tokens["esg"],
            "X-Correlation-ID": str(uuid4()),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified"] is True
    assert payload["signature_valid"] is True
    assert payload["key_version"] == "v1"
    assert payload["asym_signature_valid"] is True
    assert payload["asym_key_version"] == "v1"


@pytest.mark.asyncio
async def test_mrv_export_verification_service_success() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-api-ok",
            user_id="user-mrv-api-ok",
            vehicle_id="veh-mrv-api-ok",
            country_code="CI",
            distance_km=5.9,
            geo_hash="u0xmo",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-mrv-api-ok",
    )

    export_record = service.export_mrv_report(period="3M", correlation_id="corr-mrv-api-ok-export")
    verify_payload = service.verify_mrv_export(export_id=str(export_record.id))
    assert verify_payload["verified"] is True
    assert verify_payload["hash_valid"] is True
    assert verify_payload["signature_valid"] is True
    assert verify_payload["asym_signature_valid"] is True


@pytest.mark.asyncio
async def test_mrv_export_verification_detects_tampered_payload() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-api-tamper",
            user_id="user-mrv-api-tamper",
            vehicle_id="veh-mrv-api-tamper",
            country_code="CI",
            distance_km=7.7,
            geo_hash="u0xmt",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-mrv-api-tamper",
    )
    export_record = service.export_mrv_report(period="3M", correlation_id="corr-mrv-api-tamper-export")
    export_id = str(export_record.id)

    session_factory = get_session_local()
    with session_factory() as session:
        session.execute(
            update(EsgMrvExportModel)
            .where(EsgMrvExportModel.id == UUID(export_id))
            .values(verification_hash="f" * 64)
        )
        session.commit()

    verify_payload = service.verify_mrv_export(export_id=export_id)
    assert verify_payload["verified"] is False
    assert verify_payload["hash_valid"] is False
    assert verify_payload["signature_valid"] is False
    assert verify_payload["asym_signature_valid"] is False


@pytest.mark.asyncio
async def test_mrv_export_endpoint_returns_422_without_active_methodology() -> None:
    from src.orchestration.esg.greenos.api.router import export_mrv_report as export_mrv_handler

    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-mrv-no-method",
            user_id="user-mrv-no-method",
            vehicle_id="veh-mrv-no-method",
            country_code="CI",
            distance_km=4.9,
            geo_hash="u0xnm",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-mrv-no-method",
    )
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v2/esg/mrv/export",
            "headers": [(b"x-correlation-id", b"corr-mrv-no-method")],
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await export_mrv_handler(
            request=request,
            query=MrvExportQuery(period="3M"),
            service=service,
        )
    assert exc_info.value.status_code == 422


def test_mrv_routes_are_registered() -> None:
    from src.orchestration.esg.greenos.api.router import router as greenos_router

    paths = {route.path for route in greenos_router.routes}
    assert "/mrv/export" in paths
    assert "/mrv/export/{export_id}/verify" in paths
    assert "/mrv/export/{export_id}/confidence-summary" in paths
    assert "/mrv/methodology/current" in paths
    assert "/mrv/methodology/{version}" in paths
    assert "/impact/{trip_id}/confidence" in paths
    assert "/public-key" in paths
    assert "/internal/secrets/status" in paths


@pytest.mark.asyncio
async def test_greenos_healthcheck_is_public(async_client) -> None:
    response = await async_client.get("/api/v2/esg/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "greenos"
    assert payload["status"] == "ok"


@pytest.mark.asyncio
async def test_greenos_well_known_public_key_is_public(async_client) -> None:
    response = await async_client.get("/.well-known/greenos-public-key")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signature_algorithm"] == SIGNATURE_ALGORITHM_ED25519
    assert payload["public_key"]
    expected_fingerprint = hashlib.sha256(base64.b64decode(payload["public_key"])).hexdigest()
    assert payload["fingerprint_sha256"] == expected_fingerprint


@pytest.mark.asyncio
async def test_greenos_public_key_is_public_and_supports_external_verification(
    async_client,
    mock_auth_upsert,
) -> None:
    trip_id = "trip-public-key-verification"
    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id=trip_id,
            user_id="user-public-key-verification",
            vehicle_id="veh-public-key-verification",
            country_code="CI",
            distance_km=6.1,
            geo_hash="u0xpk",
            model_version="greenos-co2-v1",
            event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
        ),
        correlation_id="corr-public-key-verification",
    )
    record = service.get_impact(trip_id=trip_id)

    response = await async_client.get("/api/v2/esg/public-key")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signature_algorithm"] == SIGNATURE_ALGORITHM_ED25519
    assert payload["public_key"]
    expected_fingerprint = hashlib.sha256(base64.b64decode(payload["public_key"])).hexdigest()
    assert payload["fingerprint_sha256"] == expected_fingerprint

    assert (
        GreenOSSignatureService.verify_hash_with_public_key(
            hash_value=record.event_hash,
            signature=record.asym_signature,
            public_key=payload["public_key"],
        )
        is True
    )


@pytest.mark.asyncio
async def test_greenos_internal_secrets_status_requires_admin_scope(
    async_client,
    valid_tokens,
    mock_auth_upsert,
) -> None:
    response = await async_client.get(
        "/api/v2/esg/internal/secrets/status",
        headers=_secure_headers(valid_tokens["esg"]),
    )
    assert response.status_code == 403
    payload = response.json()
    error_code = payload.get("code") or payload.get("detail", {}).get("code")
    assert error_code == "GREENOS_ADMIN_SCOPE_REQUIRED"


@pytest.mark.asyncio
async def test_greenos_internal_secrets_status_returns_non_sensitive_metadata(
    async_client,
    mock_auth_upsert,
) -> None:
    admin_token = f"Bearer {jwt.encode({'sub': 'esg_admin', 'scopes': ['esg', 'admin'], 'domain': 'esg'}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)}"
    response = await async_client.get(
        "/api/v2/esg/internal/secrets/status",
        headers=_secure_headers(admin_token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] in {"env", "vault", "kms"}
    assert isinstance(payload["statuses"], dict)
    assert payload["statuses"]["GREENOS_SIGNING_SECRET"] in {"OK", "MISSING", "INVALID"}


@pytest.mark.asyncio
async def test_adversarial_mrv_export_altered_payload_returns_verify_false() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-adversarial-payload-alter",
            user_id="user-adversarial-payload-alter",
            vehicle_id="veh-adversarial-payload-alter",
            country_code="CI",
            distance_km=9.7,
            geo_hash="u0xadv1",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-adversarial-payload-alter",
    )
    export_record = service.export_mrv_report(period="3M", correlation_id="corr-adversarial-payload-export")
    export_id = str(export_record.id)

    session_factory = get_session_local()
    with session_factory() as session:
        stored_payload = session.execute(
            select(EsgMrvExportModel.payload).where(EsgMrvExportModel.id == UUID(export_id))
        ).scalar_one()
        tampered_payload = dict(stored_payload or {})
        aggregation = dict(tampered_payload.get("aggregation") or {})
        aggregation["total_co2_avoided_kg"] = float(aggregation.get("total_co2_avoided_kg", 0.0)) + 1.0
        tampered_payload["aggregation"] = aggregation
        session.execute(
            update(EsgMrvExportModel)
            .where(EsgMrvExportModel.id == UUID(export_id))
            .values(payload=tampered_payload)
        )
        session.commit()

    verification = service.verify_mrv_export(export_id=export_id)
    assert verification["verified"] is False
    assert verification["hash_valid"] is False


@pytest.mark.asyncio
async def test_adversarial_mrv_methodology_hash_mismatch_returns_verify_false() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology(methodology_version="MRV-ADVERSARIAL-2026.1")
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-adversarial-methodology-hash",
            user_id="user-adversarial-methodology-hash",
            vehicle_id="veh-adversarial-methodology-hash",
            country_code="CI",
            distance_km=8.2,
            geo_hash="u0xadv2",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-adversarial-methodology-hash",
    )
    export_record = service.export_mrv_report(period="3M", correlation_id="corr-adversarial-methodology-export")
    export_id = str(export_record.id)

    session_factory = get_session_local()
    with session_factory() as session:
        session.execute(
            update(EsgMrvExportModel)
            .where(EsgMrvExportModel.id == UUID(export_id))
            .values(methodology_hash="f" * 64)
        )
        session.commit()

    verification = service.verify_mrv_export(export_id=export_id)
    assert verification["verified"] is False
    assert verification["methodology_valid"] is False
    assert verification["hash_valid"] is True


def test_adversarial_wrong_public_key_version_fails_external_verification() -> None:
    private_v1, public_v1 = _generate_ed25519_keypair_b64()
    private_v2, public_v2 = _generate_ed25519_keypair_b64()
    service = GreenOSSignatureService(
        asym_active_key_version="v1",
        asym_private_key=private_v1,
        asym_public_key=public_v1,
        asym_private_keyring={"v1": private_v1, "v2": private_v2},
        asym_public_keyring={"v1": public_v1, "v2": public_v2},
    )
    signed = service.sign_hash_asymmetric("d" * 64)
    wrong_key = service.get_public_key(key_version="v2")

    assert signed.key_version == "v1"
    assert wrong_key.key_version == "v2"
    assert (
        GreenOSSignatureService.verify_hash_with_public_key(
            hash_value="d" * 64,
            signature=signed.signature,
            public_key=wrong_key.public_key,
        )
        is False
    )


@pytest.mark.asyncio
async def test_adversarial_mrv_export_period_overlap_returns_409() -> None:
    from src.orchestration.esg.greenos.api.router import export_mrv_report as export_mrv_handler

    service = GreenOSService()
    _create_active_mrv_methodology(methodology_version="MRV-ADVERSARIAL-OVERLAP-2026.1")
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-adversarial-overlap",
            user_id="user-adversarial-overlap",
            vehicle_id="veh-adversarial-overlap",
            country_code="CI",
            distance_km=5.8,
            geo_hash="u0xadv3",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-adversarial-overlap",
    )
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v2/esg/mrv/export",
            "headers": [(b"x-correlation-id", b"corr-adversarial-overlap-api")],
        }
    )

    first_response = await export_mrv_handler(
        request=request,
        query=MrvExportQuery(period="3M"),
        service=service,
    )
    assert first_response.export_id

    with pytest.raises(HTTPException) as exc_info:
        await export_mrv_handler(
            request=request,
            query=MrvExportQuery(period="3M"),
            service=service,
        )
    assert exc_info.value.status_code == 409
    detail = exc_info.value.detail if isinstance(exc_info.value.detail, dict) else {}
    assert detail.get("code") == "GREENOS_MRV_EXPORT_EXISTS"


@pytest.mark.asyncio
async def test_adversarial_event_replay_does_not_double_count() -> None:
    service = GreenOSService()
    _create_active_mrv_methodology(methodology_version="MRV-ADVERSARIAL-REPLAY-2026.1")
    payload = RealtimeCalculateRequest(
        trip_id="trip-adversarial-replay",
        user_id="user-adversarial-replay",
        vehicle_id="veh-adversarial-replay",
        country_code="CI",
        distance_km=4.2,
        geo_hash="u0xadv4",
        model_version="greenos-co2-v1",
        event_timestamp=datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC),
    )

    replay_results: list[bool] = []
    for idx in range(5):
        _record, idempotent = await service.calculate_realtime_impact(
            request=payload,
            correlation_id=f"corr-adversarial-replay-{idx}",
        )
        replay_results.append(idempotent)

    assert replay_results[0] is False
    assert all(item is True for item in replay_results[1:])

    session_factory = get_session_local()
    with session_factory() as session:
        ledger_count = session.execute(
            select(func.count())
            .select_from(EsgImpactLedgerModel)
            .where(EsgImpactLedgerModel.trip_id == payload.trip_id)
        ).scalar_one()
        outbox_count = session.execute(
            select(func.count()).select_from(EsgOutboxEventModel)
        ).scalar_one()
    assert ledger_count == 1
    assert outbox_count == 1

    export_record = service.export_mrv_report(period="3M", correlation_id="corr-adversarial-replay-export")
    aggregation = export_record.payload.get("aggregation", {})
    assert isinstance(aggregation, dict)
    assert aggregation.get("impacts_count") == 1


@pytest.mark.asyncio
async def test_adversarial_outbox_retry_storm_failed_dlq_and_metrics(monkeypatch) -> None:
    from src.orchestration.esg.greenos.outbox import relay_service as relay_module

    service = GreenOSService()
    await service.calculate_realtime_impact(
        request=RealtimeCalculateRequest(
            trip_id="trip-adversarial-retry-storm",
            user_id="user-adversarial-retry-storm",
            vehicle_id="veh-adversarial-retry-storm",
            country_code="CI",
            distance_km=3.9,
            geo_hash="u0xadv5",
            model_version="greenos-co2-v1",
            event_timestamp=datetime.now(UTC) - timedelta(days=1),
        ),
        correlation_id="corr-adversarial-retry-storm",
    )

    class _CounterStub:
        def __init__(self) -> None:
            self.value = 0

        def inc(self, amount: int = 1) -> None:
            self.value += amount

    class _MetricsStub:
        def __init__(self) -> None:
            self.topics: list[str] = []

        def record_dlq_event(self, topic: str) -> None:
            self.topics.append(topic)

    failed_counter = _CounterStub()
    retry_counter = _CounterStub()
    metrics_stub = _MetricsStub()
    monkeypatch.setattr(relay_module, "greenos_outbox_failed_total", failed_counter)
    monkeypatch.setattr(relay_module, "greenos_outbox_retry_total", retry_counter)
    monkeypatch.setattr(relay_module, "metrics", metrics_stub)

    class _AlwaysFailWithDlqPublisher:
        def __init__(self) -> None:
            self.dlq_calls: list[dict[str, object]] = []

        async def publish(self, **kwargs):
            _ = kwargs
            raise RuntimeError("simulated retry storm")

        async def publish_dlq(self, **kwargs):
            self.dlq_calls.append(kwargs)
            return {"ok": True}

    publisher = _AlwaysFailWithDlqPublisher()
    relay = OutboxRelayService(
        repository=GreenOSOutboxRepository(),
        publisher=publisher,
        max_retry_count=1,
        base_retry_seconds=0.0,
    )

    first_run = await relay.run_once(limit=10)
    second_run = await relay.run_once(limit=10)

    assert first_run["retried"] == 1
    assert second_run["failed"] == 1
    assert len(publisher.dlq_calls) == 1

    session_factory = get_session_local()
    with session_factory() as session:
        row = session.execute(select(EsgOutboxEventModel)).scalar_one()
        assert row.status == "FAILED"
        assert row.retry_count == 2

    assert retry_counter.value == 1
    assert failed_counter.value == 1
    assert metrics_stub.topics == [TOPIC_GREENOS_DLQ_V1]
