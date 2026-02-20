"""AOQ hook placeholders for BFOS optimization paths."""

from __future__ import annotations

from decimal import Decimal

from src.observability.logging.logger import logger


def optimize_fee(user_profile: dict | None = None) -> dict:
    """Return a deterministic default fee optimization profile."""
    profile = user_profile or {}
    logger.info(
        "event=bfos_aoq_fee_hook_applied strategy=standard",
        user_profile=str(profile),
    )
    return {
        "strategy": "standard",
        "multiplier": Decimal("1.00"),
        "reason": "aoq_placeholder_default",
    }


def optimize_fx_timing(context: dict | None = None) -> dict:
    """Return neutral FX timing advice until AOQ models are enabled."""
    _ = context or {}
    logger.info("event=bfos_aoq_fx_timing_hook_applied strategy=standard")
    return {
        "strategy": "standard",
        "rate_multiplier": Decimal("1.00"),
        "reason": "aoq_placeholder_default",
    }


def risk_adjustment(context: dict | None = None) -> dict:
    """Return neutral risk adjustment to preserve current compliance behavior."""
    _ = context or {}
    logger.info("event=bfos_aoq_risk_adjustment_hook_applied strategy=standard")
    return {
        "strategy": "standard",
        "margin_multiplier": Decimal("1.00"),
        "reason": "aoq_placeholder_default",
    }
