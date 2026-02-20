"""AOQ hooks for accounting categorization and neutral optimization."""

from __future__ import annotations

from decimal import Decimal

from src.observability.logging.logger import logger


def categorize_transaction(tx: dict) -> str:
    """Neutral categorization with deterministic fallback."""
    target = str(tx.get("target_account", "")).lower()
    status = str(tx.get("status", "")).upper()
    amount = Decimal(str(tx.get("amount", "0")))

    if "expense" in target or "charge" in target:
        category = "charge"
    elif status == "FAILED":
        category = "ignored"
    elif amount < 0:
        category = "charge"
    else:
        category = "sale"

    logger.info(
        "event=bfos_aoq_accounting_categorized",
        category=category,
        status=status,
        target_account=target,
    )
    return category


def suggest_cashflow_improvement(summary: dict) -> dict:
    """Return neutral cashflow recommendation until AOQ optimization is enabled."""
    _ = summary
    logger.info("event=bfos_aoq_cashflow_suggestion strategy=neutral")
    return {
        "strategy": "neutral",
        "action": "maintain_current_allocation",
        "reason": "aoq_accounting_placeholder",
    }


def risk_signal(summary: dict) -> dict:
    """Provide conservative neutral risk signal."""
    _ = summary
    logger.info("event=bfos_aoq_accounting_risk_signal strategy=neutral")
    return {
        "level": "normal",
        "score": Decimal("0"),
        "reason": "aoq_accounting_placeholder",
    }
