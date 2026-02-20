"""Reputation scoring engine for Tontine members."""

from __future__ import annotations

from decimal import Decimal

from src.observability.logging.logger import logger


_REPUTATION_EVENT_DELTA: dict[str, Decimal] = {
    "late_payment": Decimal("-7"),
    "regular_payment": Decimal("3"),
    "fraud_attempt": Decimal("-25"),
    "active_participation": Decimal("2"),
    "unanimous_approval": Decimal("1"),
    "unanimous_rejection": Decimal("-2"),
}


def _clamp(score: Decimal) -> Decimal:
    if score < Decimal("0"):
        return Decimal("0")
    if score > Decimal("100"):
        return Decimal("100")
    return score


class ReputationEngine:
    """Apply deterministic reputation rules in range [0,100]."""

    def adjust_reputation(self, *, current_score: Decimal, event_type: str) -> Decimal:
        delta = _REPUTATION_EVENT_DELTA.get(event_type, Decimal("0"))
        updated = _clamp((Decimal(str(current_score)) + delta).quantize(Decimal("0.01")))
        logger.info(
            "event=tontine_reputation_adjusted",
            event_type=event_type,
            previous_score=str(current_score),
            delta=str(delta),
            updated_score=str(updated),
        )
        return updated


reputation_engine = ReputationEngine()
