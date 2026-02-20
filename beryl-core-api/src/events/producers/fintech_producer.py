"""Fintech event producer with mandatory signing and schema-ready payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.events.bus.event_bus import get_event_bus
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier
from src.observability.logging.logger import logger


class FintechEventProducer:
    @staticmethod
    async def transaction_completed(
        transaction_id: str,
        user_id: str,
        amount: float,
        currency: str,
        correlation_id: str,
    ) -> None:
        topic = "fintech.transaction.completed"
        payload = {
            "event_id": str(uuid4()),
            "event_type": topic,
            "transaction_id": transaction_id,
            "actor_id": user_id,
            "amount": amount,
            "currency": currency,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }
        payload["signature"] = event_signature_verifier.sign(payload)

        bus = await get_event_bus()
        await bus.publish_raw(topic=topic, key=transaction_id, payload=payload)
        logger.info(f"event=fintech_transaction_completed_emitted tx={transaction_id}")

    @staticmethod
    async def payment_failed(
        payment_id: str,
        user_id: str,
        reason: str,
        correlation_id: str,
    ) -> None:
        topic = "fintech.payment.failed"
        payload = {
            "event_id": str(uuid4()),
            "event_type": topic,
            "payment_id": payment_id,
            "actor_id": user_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }
        payload["signature"] = event_signature_verifier.sign(payload)

        bus = await get_event_bus()
        await bus.publish_raw(topic=topic, key=payment_id, payload=payload)
        logger.info(f"event=fintech_payment_failed_emitted payment_id={payment_id}")
