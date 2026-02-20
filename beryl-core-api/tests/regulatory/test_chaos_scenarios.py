from __future__ import annotations

from pathlib import Path

from src.infrastructure.kafka.compliance.idempotency_guard import IdempotencyGuard


def test_chaos_scripts_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    required = [
        "chaos/corrupt-event-payload.sh",
        "chaos/invalid-signature.sh",
        "chaos/simulate-psp-replay.sh",
        "chaos/flood-2000-tps.sh",
        "chaos/kill-kafka-broker.sh",
        "chaos/simulate-db-loss.sh",
    ]
    for rel in required:
        path = root / rel
        assert path.exists(), f"missing chaos script: {rel}"


def test_idempotency_guard_rejects_duplicate() -> None:
    guard = IdempotencyGuard()
    assert guard.claim("chaos-event-1")
    assert not guard.claim("chaos-event-1")
