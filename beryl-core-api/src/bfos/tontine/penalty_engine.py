"""Penalty computations for Tontine default and late contribution scenarios."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from src.config.settings import settings
from src.observability.logging.logger import logger


class PenaltyEngine:
    """Compute deterministic penalties used by BTSE workflows."""

    def compute_late_payment_penalty(self, amount: Decimal) -> Decimal:
        normalized = Decimal(str(amount))
        if normalized <= 0:
            return Decimal("0.00")
        penalty = (normalized * Decimal(str(settings.bfos_tontine_late_penalty_rate))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        logger.info(
            "event=tontine_late_payment_penalty_computed",
            amount=str(normalized),
            penalty=str(penalty),
        )
        return penalty


penalty_engine = PenaltyEngine()
