"""Production-grade Kafka event bus with compliance guardrails."""

from __future__ import annotations

import asyncio
import json
import time
from importlib import import_module
from typing import Any, Callable, Dict

from src.config.settings import settings
from src.events.base.event import DomainEventType
from src.events.bus.event_bus import AbstractEventBus
from src.infrastructure.kafka.compliance import (
    MessageIntegrityValidator,
    SchemaRegistryValidator,
    SchemaValidationError,
    event_signature_verifier,
    idempotency_guard,
)
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class KafkaEventBus(AbstractEventBus):
    """Kafka transport with strict schema/signature/idempotency controls."""

    def __init__(self):
        super().__init__(broker_type="kafka")
        self.producer = None
        self.consumer = None
        self._kafka_module = None
        self._schema_validator = SchemaRegistryValidator()
        self._integrity_validator = MessageIntegrityValidator()
        self._required_signed_topics = settings.kafka_required_signed_topics_set
        self._max_publish_attempts = 5

    async def _publish_impl(
        self,
        event_type: DomainEventType,
        event_data: Dict[str, Any],
    ) -> None:
        domain = event_data.get("domain", "unknown")
        topic = f"{domain}.events"
        key = event_data.get("event_id", "no-key")
        await self._publish_raw_impl(topic=topic, key=key, payload=event_data)

    async def _publish_raw_impl(self, *, topic: str, key: str, payload: Dict[str, Any]) -> None:
        if not idempotency_guard.claim(f"publish:{topic}:{key}"):
            metrics.record_idempotency_rejection(scope="kafka_publish")
            return

        try:
            self._schema_validator.validate(topic=topic, payload=payload)
        except SchemaValidationError as exc:
            self._ensure_producer()
            self._publish_dlq(topic=topic, key=key, payload=payload, reason=f"schema_validation:{exc}")
            raise

        if topic in self._required_signed_topics and "signature" not in payload:
            metrics.record_signature_failure("missing_financial_signature")
            self._ensure_producer()
            self._publish_dlq(topic=topic, key=key, payload=payload, reason="missing_financial_signature")
            raise ValueError(f"Unsigned financial event rejected for topic {topic}")

        enriched_payload = self._integrity_validator.enrich_with_hash(payload)

        if topic in self._required_signed_topics and not event_signature_verifier.verify(enriched_payload):
            metrics.record_signature_failure("invalid_financial_signature")
            self._ensure_producer()
            self._publish_dlq(topic=topic, key=key, payload=enriched_payload, reason="invalid_financial_signature")
            raise ValueError(f"Invalid financial signature for topic {topic}")

        await asyncio.to_thread(self._send_with_retry, topic, key, enriched_payload)

    def _send_with_retry(self, topic: str, key: str, payload: dict) -> None:
        self._ensure_producer()
        assert self.producer is not None

        delay = 0.1
        last_error: Exception | None = None

        for attempt in range(1, self._max_publish_attempts + 1):
            try:
                future = self.producer.send(topic, key=key.encode("utf-8"), value=json.dumps(payload).encode("utf-8"))
                future.get(timeout=5)
                return
            except Exception as exc:  # pragma: no cover - broker-dependent
                last_error = exc
                if attempt >= self._max_publish_attempts:
                    break
                time.sleep(delay)
                delay = min(3.0, delay * 2)

        logger.error(f"event=kafka_publish_failed topic={topic} key={key} error={str(last_error)}")
        self._publish_dlq(topic=topic, key=key, payload=payload, reason=str(last_error))
        raise RuntimeError(f"kafka publish failed for {topic}")

    def _publish_dlq(self, *, topic: str, key: str, payload: dict, reason: str) -> None:
        dlq_topic = self._derive_dlq_topic(topic)
        dlq_payload = {
            "topic": topic,
            "key": key,
            "reason": reason,
            "payload": payload,
            "ts": int(time.time()),
        }
        try:
            assert self.producer is not None
            future = self.producer.send(
                dlq_topic,
                key=key.encode("utf-8"),
                value=json.dumps(dlq_payload).encode("utf-8"),
            )
            future.get(timeout=5)
            metrics.record_dlq_event(dlq_topic)
        except Exception as exc:  # pragma: no cover
            logger.error(f"event=kafka_dlq_publish_failed topic={dlq_topic} error={str(exc)}")

    def _derive_dlq_topic(self, topic: str) -> str:
        return f"{topic}.dlq"

    async def consume_batch(
        self,
        *,
        topics: list[str],
        handler: Callable[[str, dict], None],
        max_records: int = 200,
        timeout_ms: int = 1000,
    ) -> dict[str, int]:
        return await asyncio.to_thread(
            self._consume_batch_sync,
            topics,
            handler,
            max_records,
            timeout_ms,
        )

    def _consume_batch_sync(
        self,
        topics: list[str],
        handler: Callable[[str, dict], None],
        max_records: int,
        timeout_ms: int,
    ) -> dict[str, int]:
        consumer = self._build_consumer(topics)
        processed = 0
        failed = 0
        skipped = 0

        records = consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        for topic_partition, entries in records.items():
            topic = getattr(topic_partition, "topic", "unknown")
            partition = int(getattr(topic_partition, "partition", 0))
            for record in entries:
                payload = record.value
                if isinstance(payload, (bytes, bytearray)):
                    payload = json.loads(payload.decode("utf-8"))

                if topic in self._required_signed_topics and not event_signature_verifier.verify(payload):
                    metrics.record_signature_failure("consumer_invalid_signature")
                    self._publish_dlq(topic=topic, key=str(record.key), payload=payload, reason="invalid signature")
                    failed += 1
                    continue

                if not self._integrity_validator.verify_hash(payload):
                    metrics.record_signature_failure("consumer_integrity_hash_failed")
                    self._publish_dlq(topic=topic, key=str(record.key), payload=payload, reason="payload hash mismatch")
                    failed += 1
                    continue

                event_id = str(payload.get("event_id", record.offset))
                if not idempotency_guard.claim(f"consume:{topic}:{event_id}"):
                    metrics.record_idempotency_rejection(scope="kafka_consume")
                    skipped += 1
                    continue

                try:
                    handler(topic, payload)
                    processed += 1
                except Exception as exc:
                    failed += 1
                    self._publish_dlq(topic=topic, key=str(record.key), payload=payload, reason=str(exc))

            end_offset = consumer.end_offsets([topic_partition]).get(topic_partition, 0)
            position = consumer.position(topic_partition)
            lag = max(0, int(end_offset) - int(position))
            metrics.set_kafka_consumer_lag(
                topic=topic,
                partition=partition,
                group=settings.kafka_consumer_group,
                lag=lag,
            )

        if settings.kafka_manual_commit_only and (processed > 0 or skipped > 0):
            consumer.commit()

        return {
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "scanned": processed + failed + skipped,
        }

    async def _start_impl(self) -> None:
        self._ensure_producer()
        logger.info(f"event=kafka_event_bus_started bootstrap={settings.kafka_bootstrap_servers}")

    async def _stop_impl(self) -> None:
        if self.producer is not None:
            self.producer.flush()
            self.producer.close()
        if self.consumer is not None:
            self.consumer.close()
        logger.info("event=kafka_event_bus_stopped")

    def _build_consumer(self, topics: list[str]):
        self._ensure_kafka_module()
        if self.consumer is None:
            consumer_cls = getattr(self._kafka_module, "KafkaConsumer")
            self.consumer = consumer_cls(
                *topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_consumer_group,
                enable_auto_commit=not settings.kafka_manual_commit_only,
                auto_offset_reset="earliest",
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            )
        return self.consumer

    def _ensure_producer(self) -> None:
        self._ensure_kafka_module()
        if self.producer is None:
            producer_cls = getattr(self._kafka_module, "KafkaProducer")
            self.producer = producer_cls(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                acks="all",
                retries=5,
                linger_ms=5,
            )

    def _ensure_kafka_module(self) -> None:
        if self._kafka_module is not None:
            return
        try:
            self._kafka_module = import_module("kafka")
        except ModuleNotFoundError as exc:
            raise RuntimeError("kafka-python package is required for KafkaEventBus") from exc
