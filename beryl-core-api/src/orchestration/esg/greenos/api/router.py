"""GreenOS ESG v2 public API routes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.v1.errors import resolve_correlation_id
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.schemas.requests import AuditPreviewQuery, MrvExportQuery, RealtimeCalculateRequest
from src.orchestration.esg.greenos.schemas.responses import (
    AuditVerificationResponse,
    AuditPreviewResponse,
    GreenOSHealthResponse,
    ImpactConfidenceResponse,
    GreenOSPublicKeyResponse,
    GreenOSSecretsStatusResponse,
    MrvExportResponse,
    MrvExportConfidenceSummaryResponse,
    MrvMethodologyResponse,
    MrvExportVerificationResponse,
    ImpactVerificationResponse,
    ImpactRecordResponse,
    RealtimeCalculateResponse,
)
from src.orchestration.esg.greenos.services.errors import (
    CountryFactorNotConfiguredError,
    EventContractValidationError,
    GreenOSError,
    ImpactNotFoundError,
    LedgerIntegrityError,
    MrvExportAlreadyExistsError,
    MrvExportNotFoundError,
    MrvMethodologyNotFoundError,
    MrvMethodologyValidationError,
    PayloadTamperingDetectedError,
    SignatureVerificationError,
)
from src.orchestration.esg.greenos.services.greenos_service import GreenOSService


router = APIRouter()
_GREENOS_SERVICE = GreenOSService()


async def get_greenos_service() -> GreenOSService:
    """Dependency factory for GreenOS service."""
    return _GREENOS_SERVICE


def _require_admin_scope(request: Request) -> None:
    scopes = getattr(request.state, "scopes", [])
    if not isinstance(scopes, list) or "admin" not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "GREENOS_ADMIN_SCOPE_REQUIRED",
                "message": "Forbidden",
                "details": {"required_scope": "admin"},
            },
        )


@router.post("/realtime/calculate", response_model=RealtimeCalculateResponse)
async def calculate_realtime_impact(
    payload: RealtimeCalculateRequest,
    request: Request,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        record, idempotent = await service.calculate_realtime_impact(
            request=payload,
            correlation_id=correlation_id,
        )
        logger.info(
            "event=greenos_realtime_calculated",
            trip_id=payload.trip_id,
            model_version=payload.model_version,
            idempotent=idempotent,
            correlation_id=correlation_id,
        )
        return RealtimeCalculateResponse(**_impact_model_to_response(record), idempotent=idempotent)
    except CountryFactorNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "GREENOS_COUNTRY_FACTOR_NOT_CONFIGURED",
                "message": str(exc),
                "details": {"country_code": payload.country_code},
            },
        ) from exc
    except EventContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "GREENOS_EVENT_CONTRACT_INVALID",
                "message": str(exc),
                "details": {"topic": "esg_calculated.v1"},
            },
        ) from exc
    except LedgerIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "GREENOS_LEDGER_INTEGRITY_ERROR",
                "message": str(exc),
                "details": {"trip_id": payload.trip_id, "model_version": payload.model_version},
            },
        ) from exc
    except GreenOSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "GREENOS_PROCESSING_ERROR",
                "message": str(exc),
                "details": {},
            },
        ) from exc


@router.get("/impact/{trip_id}", response_model=ImpactRecordResponse)
async def get_impact_record(
    trip_id: str,
    request: Request,
    model_version: str | None = None,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        record = service.get_impact(trip_id=trip_id, model_version=model_version)
        logger.info(
            "event=greenos_impact_read",
            trip_id=trip_id,
            model_version=model_version or record.model_version,
            correlation_id=correlation_id,
        )
        return ImpactRecordResponse(**_impact_model_to_response(record))
    except ImpactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_IMPACT_NOT_FOUND",
                "message": str(exc),
                "details": {"trip_id": trip_id, "model_version": model_version},
            },
        ) from exc


@router.get("/impact/{trip_id}/confidence", response_model=ImpactConfidenceResponse)
async def get_impact_confidence(
    trip_id: str,
    request: Request,
    model_version: str | None = None,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        payload = service.get_impact_confidence(trip_id=trip_id, model_version=model_version)
        logger.info(
            "event=greenos_impact_confidence_read",
            trip_id=trip_id,
            model_version=model_version or payload["model_version"],
            correlation_id=correlation_id,
        )
        return ImpactConfidenceResponse.model_validate(payload)
    except ImpactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_IMPACT_NOT_FOUND",
                "message": str(exc),
                "details": {"trip_id": trip_id, "model_version": model_version},
            },
        ) from exc


@router.get("/audit/preview", response_model=AuditPreviewResponse)
async def get_audit_preview(
    request: Request,
    query: AuditPreviewQuery = Depends(),
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        record = await service.preview_audit(
            window=query.window,
            correlation_id=correlation_id,
            country_code=query.country_code,
        )
        logger.info(
            "event=greenos_audit_preview_generated",
            audit_id=str(record.id),
            window=query.window,
            country_code=query.country_code,
            correlation_id=correlation_id,
        )
        return AuditPreviewResponse(
            audit_id=str(record.id),
            window=record.window_label,
            window_start=record.window_start,
            window_end=record.window_end,
            country_code=record.country_code,
            methodology_id=record.methodology_id,
            model_version=record.model_version,
            report_hash=record.report_hash,
            signature=record.signature,
            signature_algorithm=record.signature_algorithm,
            key_version=record.key_version,
            trips_count=record.trips_count,
            total_distance_km=float(record.total_distance_km),
            total_co2_avoided_kg=float(record.total_co2_avoided_kg),
            payload=record.payload,
            created_at=record.created_at,
        )
    except EventContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "GREENOS_EVENT_CONTRACT_INVALID",
                "message": str(exc),
                "details": {"topic": "audit_generated.v1"},
            },
        ) from exc


@router.get("/mrv/export", response_model=MrvExportResponse)
async def export_mrv_report(
    request: Request,
    query: MrvExportQuery = Depends(),
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        record = service.export_mrv_report(period=query.period, correlation_id=correlation_id)
        logger.info(
            "event=greenos_mrv_export_api_success",
            export_id=str(record.id),
            period=query.period,
            correlation_id=correlation_id,
        )
        return MrvExportResponse(
            export_id=str(record.id),
            methodology_id=str(record.methodology_id) if record.methodology_id is not None else None,
            period=query.period,
            period_start=record.period_start,
            period_end=record.period_end,
            total_co2_avoided=float(record.total_co2_avoided),
            total_distance=float(record.total_distance),
            methodology_version=record.methodology_version,
            methodology_hash=record.methodology_hash,
            baseline_reference=record.baseline_reference,
            emission_factor_source=record.emission_factor_source,
            verification_hash=record.verification_hash,
            signature=record.signature,
            signature_algorithm=record.signature_algorithm,
            key_version=record.key_version,
            asym_signature=record.asym_signature,
            asym_algorithm=record.asym_algorithm,
            asym_key_version=record.asym_key_version,
            status=record.status,
            payload=record.payload,
            created_at=record.created_at,
        )
    except MrvExportAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "GREENOS_MRV_EXPORT_EXISTS",
                "message": str(exc),
                "details": {"period": query.period},
            },
        ) from exc
    except MrvMethodologyValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "GREENOS_MRV_METHODOLOGY_INVALID",
                "message": str(exc),
                "details": {"period": query.period},
            },
        ) from exc


@router.get("/verify/{trip_id}", response_model=ImpactVerificationResponse)
async def verify_impact_signature(
    trip_id: str,
    request: Request,
    model_version: str | None = None,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        verification = service.verify_trip_signature(trip_id=trip_id, model_version=model_version)
        if not bool(verification["event_hash_valid"]) or not bool(verification["checksum_valid"]):
            raise PayloadTamperingDetectedError("Ledger payload integrity check failed")
        if not bool(verification["signature_valid"]):
            raise SignatureVerificationError("Ledger signature verification failed")
        if not bool(verification["asym_signature_valid"]):
            raise SignatureVerificationError("Ledger asymmetric signature verification failed")
        invalid_audits = [
            item
            for item in verification["audit_results"]
            if isinstance(item, dict) and not bool(item.get("verified"))
        ]
        if invalid_audits:
            raise SignatureVerificationError("Audit signature verification failed")

        logger.info(
            "event=greenos_signature_verification_passed",
            trip_id=trip_id,
            model_version=verification["model_version"],
            audits_checked=verification["audits_checked"],
            correlation_id=correlation_id,
        )
        return ImpactVerificationResponse(
            trip_id=str(verification["trip_id"]),
            model_version=str(verification["model_version"]),
            event_hash_valid=bool(verification["event_hash_valid"]),
            checksum_valid=bool(verification["checksum_valid"]),
            signature_valid=bool(verification["signature_valid"]),
            signature_algorithm=str(verification["signature_algorithm"]),
            key_version=str(verification["key_version"]),
            asym_signature_valid=bool(verification["asym_signature_valid"]),
            asym_algorithm=str(verification["asym_algorithm"]) if verification["asym_algorithm"] is not None else None,
            asym_key_version=(
                str(verification["asym_key_version"]) if verification["asym_key_version"] is not None else None
            ),
            audits_checked=int(verification["audits_checked"]),
            audits_verified=int(verification["audits_verified"]),
            audit_results=[
                AuditVerificationResponse.model_validate(item)
                for item in verification["audit_results"]
                if isinstance(item, dict)
            ],
            verified=bool(verification["verified"]),
        )
    except ImpactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_IMPACT_NOT_FOUND",
                "message": str(exc),
                "details": {"trip_id": trip_id, "model_version": model_version},
            },
        ) from exc
    except PayloadTamperingDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "GREENOS_PAYLOAD_TAMPERED",
                "message": str(exc),
                "details": {"trip_id": trip_id, "model_version": model_version},
            },
        ) from exc
    except SignatureVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "GREENOS_INVALID_SIGNATURE",
                "message": str(exc),
                "details": {"trip_id": trip_id, "model_version": model_version},
            },
        ) from exc


@router.get("/mrv/export/{export_id}/verify", response_model=MrvExportVerificationResponse)
async def verify_mrv_export(
    export_id: str,
    request: Request,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        verification = service.verify_mrv_export(export_id=export_id)
        if not bool(verification["hash_valid"]):
            raise PayloadTamperingDetectedError("MRV export payload hash mismatch")
        if not bool(verification["signature_valid"]):
            raise SignatureVerificationError("MRV export signature verification failed")
        if not bool(verification["asym_signature_valid"]):
            raise SignatureVerificationError("MRV export asymmetric signature verification failed")
        if not bool(verification["methodology_valid"]):
            raise SignatureVerificationError("MRV export methodology mismatch")
        logger.info(
            "event=greenos_mrv_export_verify_success",
            export_id=export_id,
            correlation_id=correlation_id,
        )
        return MrvExportVerificationResponse(
            export_id=str(verification["export_id"]),
            period_start=verification["period_start"],
            period_end=verification["period_end"],
            status=str(verification["status"]),
            verification_hash=str(verification["verification_hash"]),
            hash_valid=bool(verification["hash_valid"]),
            signature_valid=bool(verification["signature_valid"]),
            asym_signature_valid=bool(verification["asym_signature_valid"]),
            methodology_valid=bool(verification["methodology_valid"]),
            signature_algorithm=str(verification["signature_algorithm"]),
            key_version=str(verification["key_version"]),
            asym_algorithm=str(verification["asym_algorithm"]) if verification["asym_algorithm"] is not None else None,
            asym_key_version=(
                str(verification["asym_key_version"]) if verification["asym_key_version"] is not None else None
            ),
            verified=bool(verification["verified"]),
        )
    except (MrvExportNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_MRV_EXPORT_NOT_FOUND",
                "message": str(exc),
                "details": {"export_id": export_id},
            },
        ) from exc
    except PayloadTamperingDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "GREENOS_MRV_PAYLOAD_TAMPERED",
                "message": str(exc),
                "details": {"export_id": export_id},
            },
        ) from exc
    except SignatureVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "GREENOS_MRV_INVALID_SIGNATURE",
                "message": str(exc),
                "details": {"export_id": export_id},
            },
        ) from exc


@router.get("/mrv/export/{export_id}/confidence-summary", response_model=MrvExportConfidenceSummaryResponse)
async def get_mrv_export_confidence_summary(
    export_id: str,
    request: Request,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        payload = service.get_mrv_export_confidence_summary(export_id=export_id)
        logger.info(
            "event=greenos_mrv_export_confidence_read",
            export_id=export_id,
            aoq_status=payload["aoq_status"],
            correlation_id=correlation_id,
        )
        return MrvExportConfidenceSummaryResponse.model_validate(payload)
    except (MrvExportNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_MRV_EXPORT_NOT_FOUND",
                "message": str(exc),
                "details": {"export_id": export_id},
            },
        ) from exc


@router.get("/mrv/methodology/current", response_model=MrvMethodologyResponse)
async def get_current_mrv_methodology(
    request: Request,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        record = service.get_current_mrv_methodology()
        logger.info(
            "event=greenos_mrv_methodology_current_read",
            methodology_version=record.methodology_version,
            correlation_id=correlation_id,
        )
        return _mrv_methodology_to_response(record)
    except MrvMethodologyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_MRV_METHODOLOGY_NOT_FOUND",
                "message": str(exc),
                "details": {"scope": "current"},
            },
        ) from exc


@router.get("/mrv/methodology/{version}", response_model=MrvMethodologyResponse)
async def get_mrv_methodology_by_version(
    version: str,
    request: Request,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        record = service.get_mrv_methodology_by_version(version=version)
        logger.info(
            "event=greenos_mrv_methodology_version_read",
            methodology_version=record.methodology_version,
            correlation_id=correlation_id,
        )
        return _mrv_methodology_to_response(record)
    except MrvMethodologyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_MRV_METHODOLOGY_NOT_FOUND",
                "message": str(exc),
                "details": {"version": version},
            },
        ) from exc


@router.get("/health", response_model=GreenOSHealthResponse)
async def greenos_healthcheck(
    service: GreenOSService = Depends(get_greenos_service),
):
    return GreenOSHealthResponse.model_validate(service.health())


@router.get("/public-key", response_model=GreenOSPublicKeyResponse)
async def get_public_key(
    request: Request,
    version: str | None = None,
    service: GreenOSService = Depends(get_greenos_service),
):
    correlation_id = resolve_correlation_id(request)
    try:
        payload = service.get_public_key(key_version=version)
        logger.info(
            "event=greenos_public_key_read",
            key_version=payload["key_version"],
            correlation_id=correlation_id,
        )
        return GreenOSPublicKeyResponse.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GREENOS_PUBLIC_KEY_NOT_FOUND",
                "message": str(exc),
                "details": {"version": version},
            },
        ) from exc


@router.get("/internal/secrets/status", response_model=GreenOSSecretsStatusResponse)
async def get_secrets_status(
    request: Request,
    service: GreenOSService = Depends(get_greenos_service),
):
    _require_admin_scope(request)
    correlation_id = resolve_correlation_id(request)
    payload = service.get_secret_provider_status()
    logger.info(
        "event=greenos_secrets_status_read",
        provider=payload["provider"],
        correlation_id=correlation_id,
    )
    return GreenOSSecretsStatusResponse.model_validate(payload)


def _impact_model_to_response(record) -> dict[str, str | float | datetime | None]:
    return {
        "id": str(record.id),
        "trip_id": record.trip_id,
        "user_id": record.user_id,
        "vehicle_id": record.vehicle_id,
        "country_code": record.country_code,
        "geo_hash": record.geo_hash,
        "distance_km": _as_float(record.distance_km),
        "co2_avoided_kg": _as_float(record.co2_avoided_kg),
        "thermal_factor_local": _as_float(record.thermal_factor_local),
        "ev_factor_local": _as_float(record.ev_factor_local),
        "model_version": record.model_version,
        "event_hash": record.event_hash,
        "checksum": record.checksum,
        "signature": record.signature,
        "signature_algorithm": record.signature_algorithm,
        "key_version": record.key_version,
        "asym_signature": record.asym_signature,
        "asym_algorithm": record.asym_algorithm,
        "asym_key_version": record.asym_key_version,
        "confidence_score": record.confidence_score,
        "integrity_index": record.integrity_index,
        "anomaly_flags": _normalize_flags(record.anomaly_flags),
        "aoq_status": record.aoq_status,
        "explanation": _normalize_explanation(record.explanation),
        "correlation_id": record.correlation_id,
        "event_timestamp": record.event_timestamp,
        "created_at": record.created_at,
    }


def _as_float(value: Decimal | float) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _normalize_flags(value: object) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None
    return [str(item) for item in value if isinstance(item, str)]


def _normalize_explanation(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def _mrv_methodology_to_response(record) -> MrvMethodologyResponse:
    return MrvMethodologyResponse(
        id=str(record.id),
        methodology_version=record.methodology_version,
        baseline_description=record.baseline_description,
        emission_factor_source=record.emission_factor_source,
        thermal_factor_reference=record.thermal_factor_reference,
        ev_factor_reference=record.ev_factor_reference,
        calculation_formula=record.calculation_formula,
        geographic_scope=record.geographic_scope,
        model_version=record.model_version,
        created_at=record.created_at,
        status=record.status,
    )
