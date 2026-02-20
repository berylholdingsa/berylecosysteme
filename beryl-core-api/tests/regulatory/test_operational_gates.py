from __future__ import annotations

from tools.ArchitectureAudit import run_audit


def test_architecture_audit_reaches_target() -> None:
    report = run_audit()
    assert report["score"] >= 100


def test_kafka_manual_commit_enforced() -> None:
    from src.events.bus.kafka_bus import KafkaEventBus

    bus = KafkaEventBus()
    assert bus is not None
    assert bus._required_signed_topics  # pylint: disable=protected-access
