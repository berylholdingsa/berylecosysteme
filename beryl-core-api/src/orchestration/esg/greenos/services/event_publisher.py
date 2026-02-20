"""Kafka publishing adapter with strict GreenOS contract validation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.events.bus.event_bus import get_event_bus
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.contracts.kafka import (
    TOPIC_AUDIT_GENERATED_V1,
    TOPIC_ESG_CALCULATED_V1,
    TOPIC_GREENOS_DLQ_V1,
    SupportedTopic,
    validate_topic_payload,
)


class GreenOSEventPublisher:
    """Publishes GreenOS events only after strict contract validation."""

    async def publish(
        self,
        *,
        topic: SupportedTopic,
        key: str,
        correlation_id: str,
        payload: dict[str, Any],
        event_id: str | None = None,
        emitted_at: datetime | None = None,
    ) -> dict[str, Any]:
        envelope = validate_topic_payload(
            topic=topic,
            payload=payload,
            correlation_id=correlation_id,
            event_id=event_id,
            emitted_at=emitted_at,
        )
        bus = await get_event_bus()
        await bus.publish_raw(topic=topic, key=key, payload=envelope)
        logger.info(
            "event=greenos_event_published",
            topic=topic,
            key=key,
            correlation_id=correlation_id,
        )
        return envelope

    async def publish_esg_calculated(
        self,
        *,
        key: str,
        correlation_id: str,
        payload: dict[str, Any],
        event_id: str | None = None,
        emitted_at: datetime | None = None,
    ) -> dict[str, Any]:
        return await self.publish(
            topic=TOPIC_ESG_CALCULATED_V1,
            key=key,
            correlation_id=correlation_id,
            payload=payload,
            event_id=event_id,
            emitted_at=emitted_at,
        )

    async def publish_audit_generated(
        self,
        *,
        key: str,
        correlation_id: str,
        payload: dict[str, Any],
        event_id: str | None = None,
        emitted_at: datetime | None = None,
    ) -> dict[str, Any]:
        return await self.publish(
            topic=TOPIC_AUDIT_GENERATED_V1,
            key=key,
            correlation_id=correlation_id,
            payload=payload,
            event_id=event_id,
            emitted_at=emitted_at,
        )

    async def publish_dlq(
        self,
        *,
        key: str,
        correlation_id: str,
        payload: dict[str, Any],
        event_id: str | None = None,
        emitted_at: datetime | None = None,
    ) -> dict[str, Any]:
        envelope = {
            "event_id": event_id or uuid4().hex,
            "topic": TOPIC_GREENOS_DLQ_V1,
            "schema_version": "v1",
            "emitted_at": (emitted_at or datetime.now(UTC)).isoformat(),
            "correlation_id": correlation_id,
            "payload": payload,
        }
        bus = await get_event_bus()
        await bus.publish_raw(topic=TOPIC_GREENOS_DLQ_V1, key=key, payload=envelope)
        logger.warning(
            "event=greenos_dlq_published",
            topic=TOPIC_GREENOS_DLQ_V1,
            key=key,
            correlation_id=correlation_id,
        )
        return envelope
