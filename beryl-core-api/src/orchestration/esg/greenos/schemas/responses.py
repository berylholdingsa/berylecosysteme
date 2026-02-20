"""Strict response DTOs for GreenOS v2 endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictResponse(BaseModel):
    """Base response schema with strict validation."""

    model_config = ConfigDict(strict=True, extra="forbid")


class ImpactRecordResponse(StrictResponse):
    """Impact ledger record returned by GreenOS APIs."""

    id: str
    trip_id: str
    user_id: str
    vehicle_id: str
    country_code: str
    geo_hash: str
    distance_km: float
    co2_avoided_kg: float
    thermal_factor_local: float
    ev_factor_local: float
    model_version: str
    event_hash: str
    checksum: str
    signature: str
    signature_algorithm: str
    key_version: str
    asym_signature: str | None
    asym_algorithm: str | None
    asym_key_version: str | None
    confidence_score: int | None
    integrity_index: int | None
    anomaly_flags: list[str] | None
    aoq_status: str | None
    explanation: dict[str, Any] | None
    correlation_id: str
    event_timestamp: datetime
    created_at: datetime


class RealtimeCalculateResponse(ImpactRecordResponse):
    """Response payload for real-time calculation endpoint."""

    idempotent: bool = Field(
        ...,
        description="True when the existing (trip_id, model_version) record was reused.",
    )


class ImpactConfidenceResponse(StrictResponse):
    """IAESG confidence detail for one impact record."""

    trip_id: str
    model_version: str
    confidence_score: int
    integrity_index: int
    anomaly_flags: list[str]
    aoq_status: str
    reasoning_summary: dict[str, Any]


class AuditPreviewResponse(StrictResponse):
    """Preview payload for audit windows (3M/6M/12M)."""

    audit_id: str
    window: str
    window_start: datetime
    window_end: datetime
    country_code: str | None
    methodology_id: str
    model_version: str
    report_hash: str
    signature: str | None
    signature_algorithm: str | None
    key_version: str | None
    trips_count: int
    total_distance_km: float
    total_co2_avoided_kg: float
    payload: dict[str, Any]
    created_at: datetime


class AuditVerificationResponse(StrictResponse):
    """Signature/hash verification details for one audit record."""

    audit_id: str
    report_hash_valid: bool
    signature_valid: bool
    signature_algorithm: str | None
    key_version: str | None
    verified: bool


class ImpactVerificationResponse(StrictResponse):
    """Signature/hash verification details for one impact trip."""

    trip_id: str
    model_version: str
    event_hash_valid: bool
    checksum_valid: bool
    signature_valid: bool
    signature_algorithm: str
    key_version: str
    asym_signature_valid: bool
    asym_algorithm: str | None
    asym_key_version: str | None
    audits_checked: int
    audits_verified: int
    audit_results: list[AuditVerificationResponse]
    verified: bool


class MrvExportResponse(StrictResponse):
    """Generated MRV export payload for a canonical reporting period."""

    export_id: str
    methodology_id: str | None
    period: str
    period_start: datetime
    period_end: datetime
    total_co2_avoided: float
    total_distance: float
    methodology_version: str
    methodology_hash: str | None
    baseline_reference: str
    emission_factor_source: str
    verification_hash: str
    signature: str
    signature_algorithm: str
    key_version: str
    asym_signature: str | None
    asym_algorithm: str | None
    asym_key_version: str | None
    status: str
    payload: dict[str, Any]
    created_at: datetime


class MrvExportVerificationResponse(StrictResponse):
    """Verification result for one MRV export artifact."""

    export_id: str
    period_start: datetime
    period_end: datetime
    status: str
    verification_hash: str
    hash_valid: bool
    signature_valid: bool
    asym_signature_valid: bool
    methodology_valid: bool
    signature_algorithm: str
    key_version: str
    asym_algorithm: str | None
    asym_key_version: str | None
    verified: bool


class MrvExportConfidenceSummaryResponse(StrictResponse):
    """IAESG confidence summary for one MRV export artifact."""

    export_id: str
    average_confidence: float
    average_integrity: float
    anomaly_flags: list[str]
    anomaly_breakdown: dict[str, int]
    aoq_status: str
    reasoning_summary: dict[str, Any]


class MrvMethodologyResponse(StrictResponse):
    """Versioned MRV methodology descriptor exposed for auditors."""

    id: str
    methodology_version: str
    baseline_description: str
    emission_factor_source: str
    thermal_factor_reference: str
    ev_factor_reference: str
    calculation_formula: str
    geographic_scope: str
    model_version: str
    created_at: datetime
    status: str


class GreenOSHealthResponse(StrictResponse):
    """Healthcheck for GreenOS v2 subsystem."""

    status: str
    service: str
    model_version: str
    topics: list[str]
    timestamp: datetime


class GreenOSPublicKeyResponse(StrictResponse):
    """Public Ed25519 key exposed for independent signature verification."""

    public_key: str
    fingerprint_sha256: str
    signature_algorithm: str
    key_version: str
    encoding: str


class GreenOSSecretsStatusResponse(StrictResponse):
    """Internal non-sensitive status for GreenOS runtime secret resolution."""

    provider: str
    cache_ttl_seconds: float
    checked_at: datetime
    statuses: dict[str, str]
