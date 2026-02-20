"""Asynchronous relay service for GreenOS outbox -> Kafka publishing."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics
from src.orchestration.esg.greenos.contracts.kafka import (
    TOPIC_AUDIT_GENERATED_V1,
    TOPIC_ESG_CALCULATED_V1,
    TOPIC_GREENOS_DLQ_V1,
)
from src.orchestration.esg.greenos.outbox.metrics import (
    greenos_outbox_failed_total,
    greenos_outbox_pending,
    greenos_outbox_retry_total,
)
from src.orchestration.esg.greenos.outbox.repository import GreenOSOutboxRepository
from src.orchestration.esg.greenos.services.event_publisher import GreenOSEventPublisher


class OutboxRelayService:
    """Publishes pending GreenOS outbox records with retry/backoff semantics."""

    def __init__(
        self,
        *,
        repository: GreenOSOutboxRepository | None = None,
        publisher: GreenOSEventPublisher | None = None,
        max_retry_count: int = 5,
        base_retry_seconds: float = 1.0,
    ) -> None:
        self._repository = repository or GreenOSOutboxRepository()
        self._publisher = publisher or GreenOSEventPublisher()
        self._max_retry_count = max_retry_count
        self._base_retry_seconds = base_retry_seconds
        self._dlq_topic = TOPIC_GREENOS_DLQ_V1

    async def run_once(self, *, limit: int = 100) -> dict[str, int]:
        """Process one batch of pending outbox rows."""
        published = 0
        retried = 0
        failed = 0
        skipped_backoff = 0
        scanned = 0
        now = datetime.now(UTC)

        with self._repository.session_factory() as session:
            greenos_outbox_pending.set(self._repository.count_pending(session=session))
            rows = self._repository.claim_pending(session=session, limit=limit)
            for row in rows:
                scanned += 1
                if not self._is_ready(row=row, now=now):
                    skipped_backoff += 1
                    continue

                payload: dict[str, Any] = dict(row.payload or {})
                correlation_id = str(payload.get("correlation_id") or f"outbox-{row.id}")
                event_payload = payload.get("event_payload")
                if not isinstance(event_payload, dict):
                    await self._publish_dlq(
                        row=row,
                        correlation_id=correlation_id,
                        reason="invalid_outbox_payload",
                        payload=payload,
                        failed_at=now,
                    )
                    self._repository.mark_failed(row=row, attempted_at=now)
                    failed += 1
                    greenos_outbox_failed_total.inc()
                    logger.error(
                        "event=greenos_outbox_invalid_payload",
                        outbox_id=str(row.id),
                        event_type=row.event_type,
                    )
                    continue
                event_payload = self._hydrate_payload(event_type=row.event_type, payload=event_payload)

                try:
                    await self._publisher.publish(
                        topic=row.event_type,
                        key=str(row.id),
                        correlation_id=correlation_id,
                        payload=event_payload,
                        event_id=str(row.id),
                    )
                    self._repository.mark_sent(row=row, attempted_at=now)
                    published += 1
                except Exception as exc:
                    if row.retry_count + 1 > self._max_retry_count:
                        await self._publish_dlq(
                            row=row,
                            correlation_id=correlation_id,
                            reason=str(exc),
                            payload=payload,
                            failed_at=now,
                        )
                        self._repository.mark_failed(row=row, attempted_at=now)
                        failed += 1
                        greenos_outbox_failed_total.inc()
                        logger.error(
                            "event=greenos_outbox_dlq",
                            outbox_id=str(row.id),
                            event_type=row.event_type,
                            retry_count=row.retry_count,
                            reason=str(exc),
                        )
                    else:
                        self._repository.mark_retry(row=row, attempted_at=now)
                        retried += 1
                        greenos_outbox_retry_total.inc()
                        logger.warning(
                            "event=greenos_outbox_retry",
                            outbox_id=str(row.id),
                            event_type=row.event_type,
                            retry_count=row.retry_count,
                            reason=str(exc),
                        )
            session.commit()
            greenos_outbox_pending.set(self._repository.count_pending(session=session))

        return {
            "scanned": scanned,
            "published": published,
            "retried": retried,
            "failed": failed,
            "skipped_backoff": skipped_backoff,
        }

    async def run_forever(self, *, poll_interval_seconds: float = 0.5, batch_size: int = 100) -> None:
        """Continuously process pending outbox rows."""
        while True:
            await self.run_once(limit=batch_size)
            await asyncio.sleep(poll_interval_seconds)

    def _is_ready(self, *, row, now: datetime) -> bool:
        if row.last_attempt_at is None:
            return True

        attempts = max(1, int(row.retry_count))
        delay_seconds = self._base_retry_seconds * (2 ** (attempts - 1))
        attempted_at = self._normalize_utc(row.last_attempt_at)
        elapsed = (now - attempted_at).total_seconds()
        return elapsed >= delay_seconds

    @staticmethod
    def _hydrate_payload(*, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        hydrated = dict(payload)
        if event_type == TOPIC_ESG_CALCULATED_V1:
            hydrated["event_timestamp"] = OutboxRelayService._parse_iso_datetime(hydrated.get("event_timestamp"))
        elif event_type == TOPIC_AUDIT_GENERATED_V1:
            hydrated["generated_at"] = OutboxRelayService._parse_iso_datetime(hydrated.get("generated_at"))
        return hydrated

    @staticmethod
    def _parse_iso_datetime(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)

    @staticmethod
    def _normalize_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    async def _publish_dlq(
        self,
        *,
        row,
        correlation_id: str,
        reason: str,
        payload: dict[str, Any],
        failed_at: datetime,
    ) -> None:
        dlq_payload = {
            "outbox_id": str(row.id),
            "aggregate_type": row.aggregate_type,
            "aggregate_id": row.aggregate_id,
            "event_type": row.event_type,
            "retry_count": int(row.retry_count) + 1,
            "reason": reason,
            "failed_at": failed_at.isoformat(),
            "payload": payload,
        }
        try:
            await self._publisher.publish_dlq(
                key=str(row.id),
                correlation_id=correlation_id,
                payload=dlq_payload,
                event_id=str(row.id),
                emitted_at=failed_at,
            )
            metrics.record_dlq_event(self._dlq_topic)
        except Exception as exc:
            logger.error(
                "event=greenos_outbox_dlq_publish_failed",
                outbox_id=str(row.id),
                event_type=row.event_type,
                reason=str(exc),
            )
