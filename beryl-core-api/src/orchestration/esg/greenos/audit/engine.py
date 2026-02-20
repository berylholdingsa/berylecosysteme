"""Audit preview engine for GreenOS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from src.db.models.esg_greenos import EsgAuditMetadataModel
from src.orchestration.esg.greenos.audit.repository import AuditMetadataInsert, AuditMetadataRepository
from src.orchestration.esg.greenos.ledger.repository import ImpactLedgerRepository
from src.orchestration.esg.greenos.services.hashing import sha256_hex
from src.orchestration.esg.greenos.services.signing import GreenOSSignatureService


AuditWindow = Literal["3M", "6M", "12M"]


@dataclass(frozen=True)
class AuditPreviewResult:
    """Domain result of an audit preview generation."""

    record: EsgAuditMetadataModel
    window_start: datetime
    window_end: datetime
    report_hash: str


class AuditEngine:
    """Builds parametric audit snapshots and persists metadata."""

    _WINDOW_TO_DAYS: dict[AuditWindow, int] = {"3M": 90, "6M": 180, "12M": 365}

    def __init__(
        self,
        *,
        ledger_repository: ImpactLedgerRepository,
        audit_repository: AuditMetadataRepository,
        methodology_id: str,
        model_version: str,
        signature_service: GreenOSSignatureService | None = None,
    ) -> None:
        self._ledger_repository = ledger_repository
        self._audit_repository = audit_repository
        self._methodology_id = methodology_id
        self._model_version = model_version
        self._signature_service = signature_service or GreenOSSignatureService()

    def preview(
        self,
        *,
        window: AuditWindow,
        correlation_id: str,
        country_code: str | None = None,
        session=None,
    ) -> AuditPreviewResult:
        now = datetime.now(UTC)
        window_start = now - timedelta(days=self._WINDOW_TO_DAYS[window])
        window_end = now

        trips_count, total_distance, total_co2 = self._ledger_repository.aggregate_window(
            window_start=window_start,
            window_end=window_end,
            country_code=country_code,
            session=session,
        )

        report_payload = {
            "window": window,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "country_code": country_code,
            "methodology_id": self._methodology_id,
            "model_version": self._model_version,
            "aggregation": {
                "trips_count": trips_count,
                "total_distance_km": float(total_distance),
                "total_co2_avoided_kg": float(total_co2),
            },
        }
        report_hash = sha256_hex(report_payload)
        signature_result = self._signature_service.sign_hash(report_hash)

        insert_payload = AuditMetadataInsert(
            window_label=window,
            window_start=window_start,
            window_end=window_end,
            country_code=country_code,
            methodology_id=self._methodology_id,
            model_version=self._model_version,
            report_hash=report_hash,
            signature=signature_result.signature,
            signature_algorithm=signature_result.signature_algorithm,
            key_version=signature_result.key_version,
            trips_count=trips_count,
            total_distance_km=Decimal(str(total_distance)),
            total_co2_avoided_kg=Decimal(str(total_co2)),
            correlation_id=correlation_id,
            payload=report_payload,
        )
        if session is None:
            record = self._audit_repository.create(insert_payload)
        else:
            record = self._audit_repository.create_in_session(session=session, payload=insert_payload)
        return AuditPreviewResult(
            record=record,
            window_start=window_start,
            window_end=window_end,
            report_hash=report_hash,
        )
