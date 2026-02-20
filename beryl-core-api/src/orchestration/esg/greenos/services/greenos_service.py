"""Orchestration service for GreenOS v2 foundation flows."""

from __future__ import annotations

import hmac
from datetime import UTC, datetime
from decimal import Decimal
import re
from typing import Literal
from uuid import UUID

from src.config.settings import settings
import json

from src.db.models.esg_greenos import (
    EsgAuditMetadataModel,
    EsgImpactLedgerModel,
    EsgMrvExportModel,
    EsgMrvMethodologyModel,
)
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.audit.engine import AuditEngine
from src.orchestration.esg.greenos.audit.repository import AuditMetadataRepository
from src.orchestration.esg.greenos.iaesg import AOQ_STATUS_REVIEW
from src.orchestration.esg.greenos.contracts.kafka import (
    TOPIC_AUDIT_GENERATED_V1,
    TOPIC_ESG_CALCULATED_V1,
    TOPIC_TRIP_COMPLETED_V1,
)
from src.orchestration.esg.greenos.ledger.repository import ImpactLedgerInsert, ImpactLedgerRepository
from src.orchestration.esg.greenos.mrv.engine import (
    MrvExportEngine,
    MrvMethodologySnapshot,
    MrvPeriod,
)
from src.orchestration.esg.greenos.mrv.metrics import (
    greenos_mrv_exports_total,
    greenos_mrv_methodology_mismatch_total,
    greenos_mrv_methodology_version_active,
    greenos_mrv_verification_failures_total,
)
from src.orchestration.esg.greenos.mrv.methodology_repository import MrvMethodologyRepository
from src.orchestration.esg.greenos.mrv.repository import MrvExportInsert, MrvExportRepository
from src.orchestration.esg.greenos.outbox.repository import GreenOSOutboxInsert, GreenOSOutboxRepository
from src.orchestration.esg.greenos.realtime.engine import RealtimeImpactEngine
from src.orchestration.esg.greenos.schemas.requests import RealtimeCalculateRequest
from src.orchestration.esg.greenos.services.errors import (
    ImpactNotFoundError,
    MrvMethodologyNotFoundError,
    MrvMethodologyValidationError,
    MrvExportNotFoundError,
)
from src.orchestration.esg.greenos.services.hashing import sha256_hex
from src.orchestration.esg.greenos.services.signing import GreenOSSignatureService, PublicKeyResult


class GreenOSService:
    """Main use-case service for GreenOS API v2."""

    def __init__(
        self,
        *,
        impact_repository: ImpactLedgerRepository | None = None,
        audit_repository: AuditMetadataRepository | None = None,
        mrv_repository: MrvExportRepository | None = None,
        methodology_repository: MrvMethodologyRepository | None = None,
        outbox_repository: GreenOSOutboxRepository | None = None,
        realtime_engine: RealtimeImpactEngine | None = None,
        mrv_engine: MrvExportEngine | None = None,
        signature_service: GreenOSSignatureService | None = None,
    ) -> None:
        self._impact_repository = impact_repository or ImpactLedgerRepository()
        self._audit_repository = audit_repository or AuditMetadataRepository()
        self._methodology_repository = methodology_repository or MrvMethodologyRepository(
            session_factory=self._impact_repository.session_factory
        )
        self._mrv_repository = mrv_repository or MrvExportRepository(session_factory=self._impact_repository.session_factory)
        self._outbox_repository = outbox_repository or GreenOSOutboxRepository(
            session_factory=self._impact_repository.session_factory
        )
        self._signature_service = signature_service or GreenOSSignatureService()
        self._realtime_engine = realtime_engine or RealtimeImpactEngine(signature_service=self._signature_service)
        self._session_factory = self._impact_repository.session_factory
        self._model_version = settings.greenos_model_version
        self._methodology_id = settings.greenos_methodology_id
        self._audit_engine = AuditEngine(
            ledger_repository=self._impact_repository,
            audit_repository=self._audit_repository,
            methodology_id=self._methodology_id,
            model_version=self._model_version,
            signature_service=self._signature_service,
        )
        self._mrv_engine = mrv_engine or MrvExportEngine(
            ledger_repository=self._impact_repository,
            signature_service=self._signature_service,
        )

    async def calculate_realtime_impact(
        self,
        *,
        request: RealtimeCalculateRequest,
        correlation_id: str,
    ) -> tuple[EsgImpactLedgerModel, bool]:
        """Calculate and persist CO2 avoided in append-only impact ledger."""
        history = self._impact_repository.list_recent_by_user(user_id=request.user_id, limit=50)
        computation = self._realtime_engine.calculate(request, history=history)
        insert_payload = ImpactLedgerInsert(
            trip_id=request.trip_id,
            user_id=request.user_id,
            vehicle_id=request.vehicle_id,
            country_code=request.country_code,
            geo_hash=request.geo_hash,
            distance_km=request.distance_km,
            co2_avoided_kg=computation.co2_avoided_kg,
            thermal_factor_local=computation.thermal_factor_local,
            ev_factor_local=computation.ev_factor_local,
            model_version=request.model_version,
            event_hash=computation.event_hash,
            checksum=computation.checksum,
            signature=computation.signature,
            signature_algorithm=computation.signature_algorithm,
            key_version=computation.key_version,
            asym_signature=computation.asym_signature,
            asym_algorithm=computation.asym_algorithm,
            asym_key_version=computation.asym_key_version,
            correlation_id=correlation_id,
            event_timestamp=computation.event_timestamp,
            confidence_score=computation.confidence_score,
            integrity_index=computation.integrity_index,
            anomaly_flags=computation.anomaly_flags,
            aoq_status=computation.aoq_status,
            explanation=computation.explanation,
        )
        with self._session_factory() as session:
            with session.begin():
                record, idempotent = self._impact_repository.create_or_get_in_session(
                    session=session,
                    payload=insert_payload,
                )
                if not idempotent:
                    self._outbox_repository.enqueue(
                        session=session,
                        payload=GreenOSOutboxInsert(
                            aggregate_type="esg_impact_ledger",
                            aggregate_id=str(record.id),
                            event_type=TOPIC_ESG_CALCULATED_V1,
                            payload={
                                "correlation_id": correlation_id,
                                "event_payload": {
                                    "ledger_id": str(record.id),
                                    "trip_id": record.trip_id,
                                    "user_id": record.user_id,
                                    "country_code": record.country_code,
                                    "co2_avoided_kg": float(record.co2_avoided_kg),
                                    "model_version": record.model_version,
                                    "checksum": record.checksum,
                                    "event_hash": record.event_hash,
                                    "signature": record.signature,
                                    "geo_hash": record.geo_hash,
                                    "event_timestamp": record.event_timestamp.isoformat(),
                                },
                            },
                        ),
                    )
            session.refresh(record)
            session.expunge(record)
        logger.info(
            "event=greenos_ledger_outbox_persisted",
            trip_id=record.trip_id,
            model_version=record.model_version,
            idempotent=idempotent,
            confidence_score=record.confidence_score,
            aoq_status=record.aoq_status,
            correlation_id=correlation_id,
        )
        return record, idempotent

    def get_impact(
        self,
        *,
        trip_id: str,
        model_version: str | None = None,
    ) -> EsgImpactLedgerModel:
        """Read impact record by trip_id."""
        record = self._impact_repository.get_by_trip_id(trip_id=trip_id, model_version=model_version)
        if record is None:
            raise ImpactNotFoundError(f"No impact record found for trip_id={trip_id}")
        return record

    def get_impact_confidence(
        self,
        *,
        trip_id: str,
        model_version: str | None = None,
    ) -> dict[str, object]:
        """Read IAESG confidence details for one impact record."""
        record = self.get_impact(trip_id=trip_id, model_version=model_version)
        confidence_score = int(record.confidence_score) if record.confidence_score is not None else 0
        integrity_index = int(record.integrity_index) if record.integrity_index is not None else 0
        anomaly_flags = self._normalize_flags(record.anomaly_flags)
        aoq_status = str(record.aoq_status or AOQ_STATUS_REVIEW)
        reasoning_summary = self._normalize_explanation(record.explanation)
        if not reasoning_summary:
            reasoning_summary = {
                "confidence_score": confidence_score,
                "integrity_index": integrity_index,
                "anomaly_flags": anomaly_flags,
                "aoq_status": aoq_status,
            }

        return {
            "trip_id": record.trip_id,
            "model_version": record.model_version,
            "confidence_score": confidence_score,
            "integrity_index": integrity_index,
            "anomaly_flags": anomaly_flags,
            "aoq_status": aoq_status,
            "reasoning_summary": reasoning_summary,
        }

    def verify_trip_signature(
        self,
        *,
        trip_id: str,
        model_version: str | None = None,
    ) -> dict[str, object]:
        """Verify ledger and related audit signatures for one trip."""
        record = self.get_impact(trip_id=trip_id, model_version=model_version)
        ledger_result = self._verify_ledger_record(record)
        related_audits = self._audit_repository.list_related_to_trip(
            event_timestamp=self._normalize_utc(record.event_timestamp),
            country_code=record.country_code,
        )
        audit_results = [self._verify_audit_record(item) for item in related_audits]
        audits_verified = sum(1 for item in audit_results if bool(item["verified"]))
        verified = bool(ledger_result["verified"]) and audits_verified == len(audit_results)

        return {
            "trip_id": record.trip_id,
            "model_version": record.model_version,
            "event_hash_valid": ledger_result["event_hash_valid"],
            "checksum_valid": ledger_result["checksum_valid"],
            "signature_valid": ledger_result["signature_valid"],
            "signature_algorithm": ledger_result["signature_algorithm"],
            "key_version": ledger_result["key_version"],
            "asym_signature_valid": ledger_result["asym_signature_valid"],
            "asym_algorithm": ledger_result["asym_algorithm"],
            "asym_key_version": ledger_result["asym_key_version"],
            "audits_checked": len(audit_results),
            "audits_verified": audits_verified,
            "audit_results": audit_results,
            "verified": verified,
        }

    async def preview_audit(
        self,
        *,
        window: Literal["3M", "6M", "12M"],
        correlation_id: str,
        country_code: str | None = None,
    ) -> EsgAuditMetadataModel:
        """Generate audit preview and persist audit metadata."""
        with self._session_factory() as session:
            with session.begin():
                preview = self._audit_engine.preview(
                    window=window,
                    correlation_id=correlation_id,
                    country_code=country_code,
                    session=session,
                )
                record = preview.record
                self._outbox_repository.enqueue(
                    session=session,
                    payload=GreenOSOutboxInsert(
                        aggregate_type="esg_audit_metadata",
                        aggregate_id=str(record.id),
                        event_type=TOPIC_AUDIT_GENERATED_V1,
                        payload={
                            "correlation_id": correlation_id,
                            "event_payload": {
                                "audit_id": str(record.id),
                                "window": record.window_label,
                                "country_code": record.country_code,
                                "methodology_id": record.methodology_id,
                                "model_version": record.model_version,
                                "report_hash": record.report_hash,
                                "trips_count": record.trips_count,
                                "total_distance_km": float(record.total_distance_km),
                                "total_co2_avoided_kg": float(record.total_co2_avoided_kg),
                                "generated_at": (record.created_at or datetime.now(UTC)).isoformat(),
                            },
                        },
                    ),
                )
            session.refresh(record)
            session.expunge(record)
        logger.info(
            "event=greenos_audit_outbox_persisted",
            audit_id=str(record.id),
            window=window,
            correlation_id=correlation_id,
        )
        return record

    def export_mrv_report(
        self,
        *,
        period: MrvPeriod,
        correlation_id: str,
    ) -> EsgMrvExportModel:
        """Create one MRV export for a canonical period window."""
        methodology = self._resolve_active_methodology()
        self._validate_methodology_for_export(methodology)
        greenos_mrv_methodology_version_active.labels(methodology_version=methodology.methodology_version).set(1)
        snapshot = self._methodology_to_snapshot(methodology)
        computation = self._mrv_engine.build_export(period=period, methodology=snapshot)
        insert_payload = MrvExportInsert(
            methodology_id=methodology.id,
            period_start=computation.period_start,
            period_end=computation.period_end,
            total_co2_avoided=computation.total_co2_avoided,
            total_distance=computation.total_distance,
            methodology_version=computation.methodology_version,
            methodology_hash=computation.methodology_hash,
            baseline_reference=computation.baseline_reference,
            emission_factor_source=computation.emission_factor_source,
            verification_hash=computation.verification_hash,
            signature=computation.signature,
            signature_algorithm=computation.signature_algorithm,
            key_version=computation.key_version,
            asym_signature=computation.asym_signature,
            asym_algorithm=computation.asym_algorithm,
            asym_key_version=computation.asym_key_version,
            payload=computation.payload,
            status=computation.status,
            confidence_score=computation.confidence_score,
            integrity_index=computation.integrity_index,
            anomaly_flags=computation.anomaly_flags,
            aoq_status=computation.aoq_status,
            explanation=computation.explanation,
        )
        record = self._mrv_repository.create(insert_payload)
        greenos_mrv_exports_total.inc()
        logger.info(
            "event=greenos_mrv_export_created",
            export_id=str(record.id),
            period=period,
            period_start=record.period_start.isoformat(),
            period_end=record.period_end.isoformat(),
            total_co2_avoided=float(record.total_co2_avoided),
            correlation_id=correlation_id,
        )
        return record

    def verify_mrv_export(
        self,
        *,
        export_id: str,
    ) -> dict[str, object]:
        """Validate stored MRV export integrity hash plus HMAC and Ed25519 signatures."""
        parsed_export_id = self._parse_uuid(export_id)
        record = self._mrv_repository.get_by_id(export_id=parsed_export_id)
        if record is None:
            raise MrvExportNotFoundError(f"No MRV export found for export_id={export_id}")

        payload = record.payload if isinstance(record.payload, dict) else {}
        hash_valid, signature_valid, asym_signature_valid = self._mrv_engine.verify_export_payload(
            payload=payload,
            verification_hash=record.verification_hash,
            signature=record.signature,
            signature_algorithm=record.signature_algorithm,
            key_version=record.key_version,
            asym_signature=record.asym_signature,
            asym_algorithm=record.asym_algorithm,
            asym_key_version=record.asym_key_version,
        )
        methodology_valid = self._verify_export_methodology_binding(record)
        verified = hash_valid and signature_valid and asym_signature_valid and methodology_valid
        if not verified:
            greenos_mrv_verification_failures_total.inc()

        return {
            "export_id": str(record.id),
            "period_start": record.period_start,
            "period_end": record.period_end,
            "status": record.status,
            "verification_hash": record.verification_hash,
            "hash_valid": hash_valid,
            "signature_valid": signature_valid,
            "asym_signature_valid": asym_signature_valid,
            "methodology_valid": methodology_valid,
            "signature_algorithm": record.signature_algorithm,
            "key_version": record.key_version,
            "asym_algorithm": record.asym_algorithm,
            "asym_key_version": record.asym_key_version,
            "verified": verified,
        }

    def get_mrv_export_confidence_summary(self, *, export_id: str) -> dict[str, object]:
        """Read IAESG confidence summary for one MRV export."""
        parsed_export_id = self._parse_uuid(export_id)
        record = self._mrv_repository.get_by_id(export_id=parsed_export_id)
        if record is None:
            raise MrvExportNotFoundError(f"No MRV export found for export_id={export_id}")

        average_confidence = float(record.confidence_score) if record.confidence_score is not None else 0.0
        average_integrity = float(record.integrity_index) if record.integrity_index is not None else 0.0
        anomaly_flags = self._normalize_flags(record.anomaly_flags)
        aoq_status = str(record.aoq_status or AOQ_STATUS_REVIEW)
        reasoning_summary = self._normalize_explanation(record.explanation)
        anomaly_breakdown = reasoning_summary.get("anomaly_breakdown")
        if not isinstance(anomaly_breakdown, dict):
            anomaly_breakdown = {flag: 1 for flag in anomaly_flags}
        normalized_breakdown = {
            str(key): int(value)
            for key, value in anomaly_breakdown.items()
            if isinstance(value, int)
        }

        if not reasoning_summary:
            reasoning_summary = {
                "average_confidence": average_confidence,
                "average_integrity": average_integrity,
                "anomaly_breakdown": normalized_breakdown,
                "aoq_status": aoq_status,
            }

        return {
            "export_id": str(record.id),
            "average_confidence": average_confidence,
            "average_integrity": average_integrity,
            "anomaly_flags": anomaly_flags,
            "anomaly_breakdown": normalized_breakdown,
            "aoq_status": aoq_status,
            "reasoning_summary": reasoning_summary,
        }

    def get_public_key(self, *, key_version: str | None = None) -> dict[str, str]:
        """Expose Ed25519 public key metadata for external verification."""
        key: PublicKeyResult = self._signature_service.get_public_key(key_version=key_version)
        return {
            "public_key": key.public_key,
            "fingerprint_sha256": key.fingerprint_sha256,
            "signature_algorithm": key.signature_algorithm,
            "key_version": key.key_version,
            "encoding": key.encoding,
        }

    def get_secret_provider_status(self) -> dict[str, object]:
        """Return non-sensitive status of runtime secret material."""
        snapshot = self._signature_service.secret_status_snapshot()
        statuses = snapshot["statuses"] if isinstance(snapshot.get("statuses"), dict) else {}
        return {
            "provider": str(snapshot.get("provider")),
            "cache_ttl_seconds": float(self._signature_service.secret_provider_cache_ttl_seconds),
            "checked_at": snapshot.get("checked_at"),
            "statuses": {str(key): str(value) for key, value in statuses.items()},
        }

    def get_current_mrv_methodology(self) -> EsgMrvMethodologyModel:
        """Return currently ACTIVE MRV methodology version."""
        record = self._methodology_repository.get_active()
        if record is None:
            raise MrvMethodologyNotFoundError("No active MRV methodology found")
        greenos_mrv_methodology_version_active.labels(methodology_version=record.methodology_version).set(1)
        return record

    def get_mrv_methodology_by_version(self, *, version: str) -> EsgMrvMethodologyModel:
        """Return MRV methodology by explicit version."""
        record = self._methodology_repository.get_by_version(version=version)
        if record is None:
            raise MrvMethodologyNotFoundError(f"MRV methodology version not found: {version}")
        return record

    def health(self) -> dict[str, object]:
        """GreenOS health response payload."""
        return {
            "status": "ok",
            "service": "greenos",
            "model_version": self._model_version,
            "topics": [
                TOPIC_TRIP_COMPLETED_V1,
                TOPIC_ESG_CALCULATED_V1,
                TOPIC_AUDIT_GENERATED_V1,
            ],
            "timestamp": datetime.now(UTC),
        }

    def _verify_ledger_record(self, record: EsgImpactLedgerModel) -> dict[str, object]:
        normalized_ts = self._normalize_utc(record.event_timestamp)
        expected_event_hash = sha256_hex(
            {
                "trip_id": record.trip_id,
                "user_id": record.user_id,
                "vehicle_id": record.vehicle_id,
                "country_code": record.country_code,
                "distance_km": float(record.distance_km),
                "thermal_factor_local": float(record.thermal_factor_local),
                "ev_factor_local": float(record.ev_factor_local),
                "co2_avoided_kg": float(record.co2_avoided_kg),
                "model_version": record.model_version,
                "geo_hash": record.geo_hash,
                "event_timestamp": normalized_ts.isoformat(),
            }
        )
        expected_checksum = sha256_hex(
            {
                "event_hash": record.event_hash,
                "trip_id": record.trip_id,
                "model_version": record.model_version,
                "country_code": record.country_code,
            }
        )
        event_hash_valid = hmac.compare_digest(expected_event_hash, record.event_hash)
        checksum_valid = hmac.compare_digest(expected_checksum, record.checksum)
        signature_valid = self._signature_service.verify_hash_signature(
            hash_value=record.event_hash,
            signature=record.signature,
            signature_algorithm=record.signature_algorithm,
            key_version=record.key_version,
        )
        asym_signature_valid = self._signature_service.verify_hash_asymmetric_signature(
            hash_value=record.event_hash,
            signature=record.asym_signature,
            signature_algorithm=record.asym_algorithm,
            key_version=record.asym_key_version,
        )
        return {
            "event_hash_valid": event_hash_valid,
            "checksum_valid": checksum_valid,
            "signature_valid": signature_valid,
            "signature_algorithm": record.signature_algorithm,
            "key_version": record.key_version,
            "asym_signature_valid": asym_signature_valid,
            "asym_algorithm": record.asym_algorithm,
            "asym_key_version": record.asym_key_version,
            "verified": event_hash_valid and checksum_valid and signature_valid and asym_signature_valid,
        }

    def _verify_audit_record(self, record: EsgAuditMetadataModel) -> dict[str, object]:
        payload = record.payload if isinstance(record.payload, dict) else {}
        expected_report_hash = sha256_hex(payload) if payload else ""
        report_hash_valid = bool(expected_report_hash) and hmac.compare_digest(expected_report_hash, record.report_hash)
        signature_valid = self._signature_service.verify_hash_signature(
            hash_value=record.report_hash,
            signature=record.signature,
            signature_algorithm=record.signature_algorithm,
            key_version=record.key_version,
        )
        return {
            "audit_id": str(record.id),
            "report_hash_valid": report_hash_valid,
            "signature_valid": signature_valid,
            "signature_algorithm": record.signature_algorithm,
            "key_version": record.key_version,
            "verified": report_hash_valid and signature_valid,
        }

    def _resolve_active_methodology(self) -> EsgMrvMethodologyModel:
        methodology = self._methodology_repository.get_active()
        if methodology is None:
            raise MrvMethodologyValidationError("Cannot export MRV without an ACTIVE methodology")
        return methodology

    def _validate_methodology_for_export(self, methodology: EsgMrvMethodologyModel) -> None:
        if not methodology.baseline_description.strip():
            raise MrvMethodologyValidationError("Cannot export MRV: baseline description is missing")
        if not methodology.emission_factor_source.strip():
            raise MrvMethodologyValidationError("Cannot export MRV: emission factor source is missing")
        if not methodology.thermal_factor_reference.strip() or not methodology.ev_factor_reference.strip():
            raise MrvMethodologyValidationError("Cannot export MRV: thermal/EV factor references are not documented")
        if not self._country_factors_documented(methodology.geographic_scope):
            raise MrvMethodologyValidationError("Cannot export MRV: country factors are not documented")

    def _verify_export_methodology_binding(self, record: EsgMrvExportModel) -> bool:
        if record.methodology_id is None or not record.methodology_hash:
            greenos_mrv_methodology_mismatch_total.inc()
            return False
        methodology = self._methodology_repository.get_by_id(methodology_id=record.methodology_id)
        if methodology is None:
            greenos_mrv_methodology_mismatch_total.inc()
            return False
        snapshot = self._methodology_to_snapshot(methodology)
        expected_hash = self._mrv_engine.methodology_hash(snapshot)
        if not hmac.compare_digest(expected_hash, record.methodology_hash):
            greenos_mrv_methodology_mismatch_total.inc()
            return False
        return True

    @staticmethod
    def _methodology_to_snapshot(record: EsgMrvMethodologyModel) -> MrvMethodologySnapshot:
        return MrvMethodologySnapshot(
            methodology_version=record.methodology_version,
            baseline_description=record.baseline_description,
            emission_factor_source=record.emission_factor_source,
            thermal_factor_reference=record.thermal_factor_reference,
            ev_factor_reference=record.ev_factor_reference,
            calculation_formula=record.calculation_formula,
            geographic_scope=record.geographic_scope,
            model_version=record.model_version,
        )

    @staticmethod
    def _country_factors_documented(geographic_scope: str) -> bool:
        raw = settings.greenos_country_factors_json
        if not raw:
            return False
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return False
        if not isinstance(parsed, dict) or not parsed:
            return False
        for country_code, value in parsed.items():
            if not isinstance(country_code, str) or len(country_code) != 2:
                return False
            if not isinstance(value, dict):
                return False
            if "thermal_factor_local" not in value or "ev_factor_local" not in value:
                return False
        required_country_codes = GreenOSService._parse_geographic_scope(geographic_scope)
        if not required_country_codes:
            return False
        documented_country_codes = {country_code.upper() for country_code in parsed.keys()}
        if not required_country_codes.issubset(documented_country_codes):
            return False
        return True

    @staticmethod
    def _parse_geographic_scope(geographic_scope: str) -> set[str]:
        return {
            token.strip().upper()
            for token in re.split(r"[,;|\s]+", geographic_scope)
            if token.strip()
        }

    @staticmethod
    def _normalize_flags(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str)]

    @staticmethod
    def _normalize_explanation(value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return {}

    @staticmethod
    def _normalize_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _parse_uuid(value: str) -> UUID:
        return UUID(value)


def to_float(value: Decimal) -> float:
    """Convert Decimal to float for API responses."""
    return float(value)
