from __future__ import annotations

from src.events.bus.kafka_bus import KafkaEventBus
from src.events.outbox_relay import outbox_relay_service
from src.observability.metrics.prometheus import metrics


def test_dlq_topic_naming_contract() -> None:
    bus = KafkaEventBus()
    assert bus._derive_dlq_topic("fintech.transaction.completed") == "fintech.transaction.completed.dlq"  # pylint: disable=protected-access


def test_outbox_relay_exposes_dlq_counter_method() -> None:
    assert callable(getattr(outbox_relay_service, "dlq_count", None))


def test_dlq_metric_is_registered() -> None:
    assert hasattr(metrics, "dlq_events_total")
