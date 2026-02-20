"""Real-time GreenOS CO2 avoided computation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from src.config.settings import settings
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.iaesg import (
    build_reasoning_summary,
    compute_confidence_score,
    compute_integrity_index,
    detect_anomalies,
    evaluate_aoq,
    extract_basic_features,
    extract_historical_features,
    extract_temporal_features,
    record_iaesg_evaluation,
)
from src.orchestration.esg.greenos.schemas.requests import RealtimeCalculateRequest
from src.orchestration.esg.greenos.services.errors import CountryFactorNotConfiguredError
from src.orchestration.esg.greenos.services.hashing import sha256_hex
from src.orchestration.esg.greenos.services.signing import GreenOSSignatureService


@dataclass(frozen=True)
class CountryFactorSet:
    """Country-level thermal/electricity factors used for CO2 computation."""

    thermal_factor_local: float
    ev_factor_local: float


@dataclass(frozen=True)
class RealtimeComputation:
    """Calculated GreenOS result plus deterministic hash material."""

    co2_avoided_kg: float
    thermal_factor_local: float
    ev_factor_local: float
    event_hash: str
    checksum: str
    signature: str
    signature_algorithm: str
    key_version: str
    asym_signature: str
    asym_algorithm: str
    asym_key_version: str
    confidence_score: int
    integrity_index: int
    anomaly_flags: list[str]
    aoq_status: str
    explanation: dict[str, object]
    event_timestamp: datetime


class RealtimeImpactEngine:
    """Computes avoided CO2 in strict, deterministic mode."""

    def __init__(
        self,
        *,
        country_factors: Mapping[str, CountryFactorSet] | None = None,
        default_model_version: str | None = None,
        signature_service: GreenOSSignatureService | None = None,
    ) -> None:
        self._country_factors = dict(country_factors) if country_factors is not None else self._load_country_factors()
        self._default_model_version = default_model_version or settings.greenos_model_version
        self._signature_service = signature_service or GreenOSSignatureService()

    def calculate(
        self,
        request: RealtimeCalculateRequest,
        *,
        history: list[object] | None = None,
    ) -> RealtimeComputation:
        factors = self._country_factors.get(request.country_code)
        if factors is None:
            raise CountryFactorNotConfiguredError(
                f"No country factors configured for country_code={request.country_code}"
            )

        event_timestamp = request.event_timestamp or datetime.now(UTC)
        co2_avoided = (request.distance_km * factors.thermal_factor_local) - (
            request.distance_km * factors.ev_factor_local
        )
        co2_avoided = round(co2_avoided, 6)
        model_version = request.model_version or self._default_model_version

        hash_payload: dict[str, Any] = {
            "trip_id": request.trip_id,
            "user_id": request.user_id,
            "vehicle_id": request.vehicle_id,
            "country_code": request.country_code,
            "distance_km": request.distance_km,
            "thermal_factor_local": factors.thermal_factor_local,
            "ev_factor_local": factors.ev_factor_local,
            "co2_avoided_kg": co2_avoided,
            "model_version": model_version,
            "geo_hash": request.geo_hash,
            "event_timestamp": event_timestamp.isoformat(),
        }
        event_hash = sha256_hex(hash_payload)
        checksum = sha256_hex(
            {
                "event_hash": event_hash,
                "trip_id": request.trip_id,
                "model_version": model_version,
                "country_code": request.country_code,
            }
        )
        signature_result = self._signature_service.sign_hash(event_hash)
        asym_signature_result = self._signature_service.sign_hash_asymmetric(event_hash)
        historical_records = list(history or [])
        iaesg_input = self._build_iaesg_input(
            request=request,
            event_timestamp=event_timestamp,
            co2_avoided_kg=co2_avoided,
            factors=factors,
            model_version=model_version,
            history=historical_records,
        )
        features: dict[str, Any] = {}
        features.update(extract_basic_features(iaesg_input))
        features.update(extract_temporal_features(iaesg_input))
        features.update(extract_historical_features(iaesg_input, historical_records))
        confidence_score = compute_confidence_score(features)
        integrity_index = compute_integrity_index(features)
        anomaly_flags = detect_anomalies(features)
        aoq_status = evaluate_aoq(confidence_score=confidence_score, anomaly_flags=anomaly_flags)
        explanation = build_reasoning_summary(
            features=features,
            confidence_score=confidence_score,
            integrity_index=integrity_index,
            anomaly_flags=anomaly_flags,
            aoq_status=aoq_status,
        )
        record_iaesg_evaluation(anomaly_flags=anomaly_flags, aoq_status=aoq_status)
        logger.info(
            "event=greenos_iaesg_evaluated",
            trip_id=request.trip_id,
            model_version=model_version,
            confidence_score=confidence_score,
            integrity_index=integrity_index,
            aoq_status=aoq_status,
            anomaly_flags=anomaly_flags,
        )

        return RealtimeComputation(
            co2_avoided_kg=co2_avoided,
            thermal_factor_local=factors.thermal_factor_local,
            ev_factor_local=factors.ev_factor_local,
            event_hash=event_hash,
            checksum=checksum,
            signature=signature_result.signature,
            signature_algorithm=signature_result.signature_algorithm,
            key_version=signature_result.key_version,
            asym_signature=asym_signature_result.signature,
            asym_algorithm=asym_signature_result.signature_algorithm,
            asym_key_version=asym_signature_result.key_version,
            confidence_score=confidence_score,
            integrity_index=integrity_index,
            anomaly_flags=anomaly_flags,
            aoq_status=aoq_status,
            explanation=explanation,
            event_timestamp=event_timestamp,
        )

    def _load_country_factors(self) -> dict[str, CountryFactorSet]:
        try:
            raw = json.loads(settings.greenos_country_factors_json)
        except json.JSONDecodeError as exc:
            raise CountryFactorNotConfiguredError("Invalid GREENOS_COUNTRY_FACTORS_JSON") from exc

        if not isinstance(raw, dict) or not raw:
            raise CountryFactorNotConfiguredError("GREENOS_COUNTRY_FACTORS_JSON must contain at least one country")

        parsed: dict[str, CountryFactorSet] = {}
        for key, value in raw.items():
            if not isinstance(key, str):
                raise CountryFactorNotConfiguredError("Country factor key must be a string")
            country_code = key.upper()
            if len(country_code) != 2 or not country_code.isalpha():
                raise CountryFactorNotConfiguredError(f"Invalid country key '{key}' in GREENOS_COUNTRY_FACTORS_JSON")
            if not isinstance(value, dict):
                raise CountryFactorNotConfiguredError(f"Invalid factor object for country {country_code}")
            if "thermal_factor_local" not in value or "ev_factor_local" not in value:
                raise CountryFactorNotConfiguredError(
                    f"Missing required factor fields for country {country_code}"
                )
            thermal = float(value["thermal_factor_local"])
            ev = float(value["ev_factor_local"])
            if thermal <= 0 or ev < 0:
                raise CountryFactorNotConfiguredError(
                    f"Invalid factor values for country {country_code}: thermal={thermal}, ev={ev}"
                )
            parsed[country_code] = CountryFactorSet(thermal_factor_local=thermal, ev_factor_local=ev)

        return parsed

    @staticmethod
    def _build_iaesg_input(
        *,
        request: RealtimeCalculateRequest,
        event_timestamp: datetime,
        co2_avoided_kg: float,
        factors: CountryFactorSet,
        model_version: str,
        history: list[object],
    ) -> dict[str, Any]:
        previous_event_timestamp: datetime | None = None
        previous_distance_km: float | None = None
        recent_event_count = 0

        for item in history:
            item_ts = RealtimeImpactEngine._read_datetime(item, "event_timestamp")
            if item_ts is None:
                continue
            if item_ts <= event_timestamp and (event_timestamp - item_ts).total_seconds() <= 3600:
                recent_event_count += 1
            if item_ts <= event_timestamp and (
                previous_event_timestamp is None or item_ts > previous_event_timestamp
            ):
                previous_event_timestamp = item_ts
                previous_distance_km = RealtimeImpactEngine._read_float(item, "distance_km")

        return {
            "trip_id": request.trip_id,
            "user_id": request.user_id,
            "vehicle_id": request.vehicle_id,
            "country_code": request.country_code,
            "geo_hash": request.geo_hash,
            "distance_km": request.distance_km,
            "co2_avoided_kg": co2_avoided_kg,
            "thermal_factor_local": factors.thermal_factor_local,
            "ev_factor_local": factors.ev_factor_local,
            "model_version": model_version,
            "methodology_version": model_version,
            "event_timestamp": event_timestamp,
            "previous_event_timestamp": previous_event_timestamp,
            "previous_distance_km": previous_distance_km,
            "recent_event_count": recent_event_count,
            "crypto_integrity_ok": True,
        }

    @staticmethod
    def _read_value(item: object, field_name: str) -> Any:
        if isinstance(item, Mapping):
            return item.get(field_name)
        return getattr(item, field_name, None)

    @staticmethod
    def _read_float(item: object, field_name: str) -> float | None:
        raw = RealtimeImpactEngine._read_value(item, field_name)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _read_datetime(item: object, field_name: str) -> datetime | None:
        raw = RealtimeImpactEngine._read_value(item, field_name)
        if raw is None:
            return None
        if isinstance(raw, datetime):
            if raw.tzinfo is None:
                return raw.replace(tzinfo=UTC)
            return raw.astimezone(UTC)
        if isinstance(raw, str):
            normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        return None
