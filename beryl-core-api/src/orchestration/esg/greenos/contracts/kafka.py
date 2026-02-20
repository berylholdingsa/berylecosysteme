"""Strict, versioned Kafka event contracts for GreenOS."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, ValidationError

from src.orchestration.esg.greenos.services.errors import EventContractValidationError

TOPIC_TRIP_COMPLETED_V1 = "trip_completed.v1"
TOPIC_ESG_CALCULATED_V1 = "esg_calculated.v1"
TOPIC_AUDIT_GENERATED_V1 = "audit_generated.v1"
TOPIC_GREENOS_DLQ_V1 = "esg_greenos.dlq.v1"

SupportedTopic = Literal[
    TOPIC_TRIP_COMPLETED_V1,
    TOPIC_ESG_CALCULATED_V1,
    TOPIC_AUDIT_GENERATED_V1,
]


class StrictContract(BaseModel):
    """Contract base model with strict validation."""

    model_config = ConfigDict(strict=True, extra="forbid")


class TripCompletedPayloadV1(StrictContract):
    trip_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    vehicle_id: str = Field(..., min_length=1, max_length=128)
    country_code: str = Field(..., min_length=2, max_length=2)
    distance_km: PositiveFloat
    geo_hash: str = Field(..., min_length=4, max_length=32)
    event_timestamp: datetime


class EsgCalculatedPayloadV1(StrictContract):
    ledger_id: str = Field(..., min_length=1, max_length=64)
    trip_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    country_code: str = Field(..., min_length=2, max_length=2)
    co2_avoided_kg: float
    model_version: str = Field(..., min_length=1, max_length=64)
    checksum: str = Field(..., min_length=32, max_length=128)
    event_hash: str = Field(..., min_length=32, max_length=128)
    signature: str = Field(..., min_length=32, max_length=128)
    geo_hash: str = Field(..., min_length=4, max_length=32)
    event_timestamp: datetime


class AuditGeneratedPayloadV1(StrictContract):
    audit_id: str = Field(..., min_length=1, max_length=64)
    window: Literal["3M", "6M", "12M"]
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    methodology_id: str = Field(..., min_length=1, max_length=64)
    model_version: str = Field(..., min_length=1, max_length=64)
    report_hash: str = Field(..., min_length=32, max_length=128)
    trips_count: int = Field(..., ge=0)
    total_distance_km: float
    total_co2_avoided_kg: float
    generated_at: datetime


class TripCompletedEnvelopeV1(StrictContract):
    event_id: str = Field(..., min_length=1, max_length=64)
    topic: Literal[TOPIC_TRIP_COMPLETED_V1]
    schema_version: Literal["v1"] = "v1"
    emitted_at: datetime
    correlation_id: str = Field(..., min_length=1, max_length=128)
    payload: TripCompletedPayloadV1


class EsgCalculatedEnvelopeV1(StrictContract):
    event_id: str = Field(..., min_length=1, max_length=64)
    topic: Literal[TOPIC_ESG_CALCULATED_V1]
    schema_version: Literal["v1"] = "v1"
    emitted_at: datetime
    correlation_id: str = Field(..., min_length=1, max_length=128)
    payload: EsgCalculatedPayloadV1


class AuditGeneratedEnvelopeV1(StrictContract):
    event_id: str = Field(..., min_length=1, max_length=64)
    topic: Literal[TOPIC_AUDIT_GENERATED_V1]
    schema_version: Literal["v1"] = "v1"
    emitted_at: datetime
    correlation_id: str = Field(..., min_length=1, max_length=128)
    payload: AuditGeneratedPayloadV1


def validate_topic_payload(
    *,
    topic: SupportedTopic,
    payload: dict[str, Any],
    correlation_id: str,
    event_id: str | None = None,
    emitted_at: datetime | None = None,
) -> dict[str, Any]:
    """Validate and build strict event envelope for a versioned topic."""
    envelope_base: dict[str, Any] = {
        "event_id": event_id or uuid4().hex,
        "topic": topic,
        "schema_version": "v1",
        "emitted_at": emitted_at or datetime.now(UTC),
        "correlation_id": correlation_id,
        "payload": payload,
    }
    try:
        if topic == TOPIC_TRIP_COMPLETED_V1:
            return TripCompletedEnvelopeV1.model_validate(envelope_base).model_dump(mode="json")
        if topic == TOPIC_ESG_CALCULATED_V1:
            return EsgCalculatedEnvelopeV1.model_validate(envelope_base).model_dump(mode="json")
        if topic == TOPIC_AUDIT_GENERATED_V1:
            return AuditGeneratedEnvelopeV1.model_validate(envelope_base).model_dump(mode="json")
        raise EventContractValidationError(f"Unsupported topic: {topic}")
    except ValidationError as exc:
        raise EventContractValidationError(f"Invalid payload for topic {topic}: {exc}") from exc
