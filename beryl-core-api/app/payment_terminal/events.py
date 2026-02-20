"""Event helpers for payment terminal topics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from src.events.outbox_relay import outbox_relay_service
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier


TOPIC_PAYMENT_INITIATED = "payment_initiated"
TOPIC_PAYMENT_CONFIRMED = "payment_confirmed"
TOPIC_PAYMENT_BLOCKED = "payment_blocked"
TOPIC_PAYMENT_FLAGGED = "payment_flagged"


def _deterministic_event_id(*, topic: str, transaction_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"payment-terminal:{topic}:{transaction_id}"))


def build_payment_event_payload(
    *,
    topic: str,
    transaction_id: str,
    correlation_id: str,
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_id": _deterministic_event_id(topic=topic, transaction_id=transaction_id),
        "event_type": topic,
        "transaction_id": transaction_id,
        "correlation_id": correlation_id,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }


def stage_payment_event(
    *,
    session,
    topic: str,
    transaction_id: str,
    correlation_id: str,
    request_id: str,
    payload: dict[str, Any],
) -> None:
    event_payload = build_payment_event_payload(
        topic=topic,
        transaction_id=transaction_id,
        correlation_id=correlation_id,
        request_id=request_id,
        payload=payload,
    )
    signature = event_signature_verifier.sign(event_payload)
    outbox_relay_service.stage_event(
        session=session,
        topic=topic,
        event_key=transaction_id,
        payload=event_payload,
        signature=signature,
    )

