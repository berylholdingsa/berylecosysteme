"""MRV export engine for GreenOS climate reporting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hmac
from typing import Any, Literal

from src.db.models.esg_greenos import EsgImpactLedgerModel
from src.orchestration.esg.greenos.iaesg import AOQ_STATUS_REVIEW, evaluate_aoq
from src.orchestration.esg.greenos.ledger.repository import ImpactLedgerRepository
from src.orchestration.esg.greenos.mrv.canonical import sha256_hex_strict
from src.orchestration.esg.greenos.services.signing import GreenOSSignatureService


MrvPeriod = Literal["3M", "6M", "12M"]


@dataclass(frozen=True)
class MrvMethodologySnapshot:
    """Immutable methodology projection used during MRV export computation."""

    methodology_version: str
    baseline_description: str
    emission_factor_source: str
    thermal_factor_reference: str
    ev_factor_reference: str
    calculation_formula: str
    geographic_scope: str
    model_version: str


@dataclass(frozen=True)
class MrvExportComputation:
    """Computed MRV export data ready for persistence."""

    period_start: datetime
    period_end: datetime
    total_co2_avoided: Decimal
    total_distance: Decimal
    methodology_version: str
    methodology_hash: str
    baseline_reference: str
    emission_factor_source: str
    verification_hash: str
    signature: str
    signature_algorithm: str
    key_version: str
    asym_signature: str
    asym_algorithm: str
    asym_key_version: str
    confidence_score: int | None
    integrity_index: int | None
    anomaly_flags: list[str]
    aoq_status: str | None
    explanation: dict[str, object]
    payload: dict[str, object]
    status: str


class MrvExportEngine:
    """Builds deterministic MRV payloads and signs their verification hash."""

    _WINDOW_TO_DAYS: dict[MrvPeriod, int] = {"3M": 90, "6M": 180, "12M": 365}

    def __init__(
        self,
        *,
        ledger_repository: ImpactLedgerRepository,
        signature_service: GreenOSSignatureService | None = None,
    ) -> None:
        self._ledger_repository = ledger_repository
        self._signature_service = signature_service or GreenOSSignatureService()

    def build_export(
        self,
        *,
        period: MrvPeriod,
        methodology: MrvMethodologySnapshot,
        reference_time: datetime | None = None,
    ) -> MrvExportComputation:
        period_start, period_end = self.resolve_period_bounds(period=period, reference_time=reference_time)
        rows = self._ledger_repository.list_window(window_start=period_start, window_end=period_end)
        selected_rows, proof = self._deduplicate_trip_records(rows)
        confidence_score, integrity_index, anomaly_flags, aoq_status, explanation = self._summarize_iaesg(selected_rows)

        total_distance = sum((row.distance_km for row in selected_rows), Decimal("0"))
        total_co2_avoided = sum((row.co2_avoided_kg for row in selected_rows), Decimal("0"))
        payload = self._build_payload(
            period=period,
            period_start=period_start,
            period_end=period_end,
            selected_rows=selected_rows,
            methodology=methodology,
            total_distance=total_distance,
            total_co2_avoided=total_co2_avoided,
            non_double_counting_proof=proof,
            confidence_score=confidence_score,
            integrity_index=integrity_index,
            anomaly_flags=anomaly_flags,
            aoq_status=aoq_status,
            explanation=explanation,
        )
        verification_hash = sha256_hex_strict(payload)
        methodology_hash = self.methodology_hash(methodology)
        signature_result = self._signature_service.sign_hash(verification_hash)
        asym_signature_result = self._signature_service.sign_hash_asymmetric(verification_hash)

        return MrvExportComputation(
            period_start=period_start,
            period_end=period_end,
            total_co2_avoided=total_co2_avoided,
            total_distance=total_distance,
            methodology_version=methodology.methodology_version,
            methodology_hash=methodology_hash,
            baseline_reference=methodology.baseline_description,
            emission_factor_source=methodology.emission_factor_source,
            verification_hash=verification_hash,
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
            payload=payload,
            status="EXPORTED",
        )

    def verify_export_payload(
        self,
        *,
        payload: dict[str, object],
        verification_hash: str,
        signature: str | None,
        signature_algorithm: str | None,
        key_version: str | None,
        asym_signature: str | None,
        asym_algorithm: str | None,
        asym_key_version: str | None,
    ) -> tuple[bool, bool, bool]:
        expected_hash = sha256_hex_strict(payload)
        hash_valid = hmac.compare_digest(expected_hash, verification_hash)
        signature_valid = self._signature_service.verify_hash_signature(
            hash_value=verification_hash,
            signature=signature,
            signature_algorithm=signature_algorithm,
            key_version=key_version,
        )
        asym_signature_valid = self._signature_service.verify_hash_asymmetric_signature(
            hash_value=verification_hash,
            signature=asym_signature,
            signature_algorithm=asym_algorithm,
            key_version=asym_key_version,
        )
        return hash_valid, signature_valid, asym_signature_valid

    @staticmethod
    def methodology_hash(methodology: MrvMethodologySnapshot) -> str:
        payload = {
            "methodology_version": methodology.methodology_version,
            "baseline_description": methodology.baseline_description,
            "emission_factor_source": methodology.emission_factor_source,
            "thermal_factor_reference": methodology.thermal_factor_reference,
            "ev_factor_reference": methodology.ev_factor_reference,
            "calculation_formula": methodology.calculation_formula,
            "geographic_scope": methodology.geographic_scope,
            "model_version": methodology.model_version,
        }
        return sha256_hex_strict(payload)

    def resolve_period_bounds(
        self,
        *,
        period: MrvPeriod,
        reference_time: datetime | None = None,
    ) -> tuple[datetime, datetime]:
        days = self._WINDOW_TO_DAYS[period]
        now = self._normalize_utc(reference_time or datetime.now(UTC))
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = period_end - timedelta(days=days)
        return period_start, period_end

    def _build_payload(
        self,
        *,
        period: MrvPeriod,
        period_start: datetime,
        period_end: datetime,
        selected_rows: list[EsgImpactLedgerModel],
        methodology: MrvMethodologySnapshot,
        total_distance: Decimal,
        total_co2_avoided: Decimal,
        non_double_counting_proof: dict[str, object],
        confidence_score: int,
        integrity_index: int,
        anomaly_flags: list[str],
        aoq_status: str,
        explanation: dict[str, object],
    ) -> dict[str, object]:
        impacts = [
            {
                "trip_id": row.trip_id,
                "model_version": row.model_version,
                "country_code": row.country_code,
                "distance_km": float(row.distance_km),
                "co2_avoided_kg": float(row.co2_avoided_kg),
                "event_hash": row.event_hash,
                "checksum": row.checksum,
                "signature": row.signature,
                "signature_algorithm": row.signature_algorithm,
                "key_version": row.key_version,
                "asym_signature": row.asym_signature,
                "asym_algorithm": row.asym_algorithm,
                "asym_key_version": row.asym_key_version,
                "confidence_score": row.confidence_score,
                "integrity_index": row.integrity_index,
                "anomaly_flags": self._normalize_flags(row.anomaly_flags),
                "aoq_status": row.aoq_status,
                "explanation": self._normalize_explanation(row.explanation),
                "event_timestamp": self._normalize_utc(row.event_timestamp).isoformat(),
            }
            for row in selected_rows
        ]
        model_versions = sorted({row.model_version for row in selected_rows})
        country_factors_used = self._collect_country_factors(selected_rows)
        payload: dict[str, object] = {
            "period": period,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "generated_at": period_end.isoformat(),
            "methodology": {
                "methodology_version": methodology.methodology_version,
                "baseline_description": methodology.baseline_description,
                "emission_factor_source": methodology.emission_factor_source,
                "thermal_factor_reference": methodology.thermal_factor_reference,
                "ev_factor_reference": methodology.ev_factor_reference,
                "calculation_formula": methodology.calculation_formula,
                "geographic_scope": methodology.geographic_scope,
                "model_version": methodology.model_version,
            },
            "country_factors_used": country_factors_used,
            "model_versions": model_versions,
            "aggregation": {
                "impacts_count": len(impacts),
                "total_distance_km": float(total_distance),
                "total_co2_avoided_kg": float(total_co2_avoided),
            },
            "confidence_summary": {
                "average_confidence": confidence_score,
                "average_integrity": integrity_index,
                "anomaly_flags": anomaly_flags,
                "anomaly_breakdown": explanation.get("anomaly_breakdown", {}),
                "aoq_status": aoq_status,
            },
            "impacts": impacts,
            "non_double_counting_proof": non_double_counting_proof,
        }
        return payload

    @staticmethod
    def _collect_country_factors(rows: list[EsgImpactLedgerModel]) -> dict[str, object]:
        by_country: dict[str, list[EsgImpactLedgerModel]] = {}
        for row in rows:
            by_country.setdefault(row.country_code, []).append(row)

        factors: dict[str, object] = {}
        for country_code, country_rows in sorted(by_country.items(), key=lambda item: item[0]):
            unique_pairs = sorted(
                {
                    (
                        float(item.thermal_factor_local),
                        float(item.ev_factor_local),
                    )
                    for item in country_rows
                }
            )
            factors[country_code] = {
                "trip_count": len(country_rows),
                "factors": [
                    {"thermal_factor_local": pair[0], "ev_factor_local": pair[1]}
                    for pair in unique_pairs
                ],
            }
        return factors

    @staticmethod
    def _deduplicate_trip_records(rows: list[EsgImpactLedgerModel]) -> tuple[list[EsgImpactLedgerModel], dict[str, object]]:
        sorted_rows = sorted(
            rows,
            key=lambda item: (
                item.trip_id,
                MrvExportEngine._normalize_utc(item.created_at),
                MrvExportEngine._normalize_utc(item.event_timestamp),
            ),
            reverse=True,
        )
        selected_by_trip: dict[str, EsgImpactLedgerModel] = {}
        dropped_rows: list[EsgImpactLedgerModel] = []

        for row in sorted_rows:
            existing = selected_by_trip.get(row.trip_id)
            if existing is None:
                selected_by_trip[row.trip_id] = row
                continue
            dropped_rows.append(row)

        selected_rows = sorted(
            selected_by_trip.values(),
            key=lambda item: (
                MrvExportEngine._normalize_utc(item.event_timestamp),
                item.trip_id,
                item.model_version,
            ),
        )
        dropped_trip_counts = Counter(item.trip_id for item in dropped_rows)
        duplicate_trip_ids = sorted(dropped_trip_counts.keys())
        proof_payload = {
            "raw_impacts_count": len(rows),
            "selected_impacts_count": len(selected_rows),
            "duplicates_removed_count": len(dropped_rows),
            "duplicate_trip_ids": duplicate_trip_ids,
            "duplicate_trip_frequencies": {trip_id: dropped_trip_counts[trip_id] for trip_id in duplicate_trip_ids},
            "deduplication_rule": "latest_created_at_per_trip_id",
        }
        proof = dict(proof_payload)
        proof["proof_hash"] = sha256_hex_strict(proof_payload)
        proof["double_counting_blocked"] = len(dropped_rows) == (len(rows) - len(selected_rows))
        return selected_rows, proof

    def _summarize_iaesg(
        self,
        rows: list[EsgImpactLedgerModel],
    ) -> tuple[int, int, list[str], str, dict[str, object]]:
        confidence_values = [int(row.confidence_score) for row in rows if row.confidence_score is not None]
        integrity_values = [int(row.integrity_index) for row in rows if row.integrity_index is not None]

        average_confidence = 50 if not confidence_values else int(round(sum(confidence_values) / len(confidence_values)))
        average_integrity = 50 if not integrity_values else int(round(sum(integrity_values) / len(integrity_values)))

        breakdown_counter: Counter[str] = Counter()
        for row in rows:
            for flag in self._normalize_flags(row.anomaly_flags):
                breakdown_counter[flag] += 1

        anomaly_flags = sorted(breakdown_counter.keys())
        aoq_status = AOQ_STATUS_REVIEW if not rows else evaluate_aoq(average_confidence, anomaly_flags)
        explanation: dict[str, object] = {
            "impacts_count": len(rows),
            "scored_impacts_count": len(confidence_values),
            "average_confidence": average_confidence,
            "average_integrity": average_integrity,
            "anomaly_breakdown": {
                key: int(breakdown_counter[key])
                for key in sorted(breakdown_counter.keys())
            },
        }
        return average_confidence, average_integrity, anomaly_flags, aoq_status, explanation

    @staticmethod
    def _normalize_flags(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str)]

    @staticmethod
    def _normalize_explanation(value: Any) -> dict[str, object]:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return {}

    @staticmethod
    def _normalize_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
