"""Revenue analytics helpers for BFOS reporting."""

from __future__ import annotations

from decimal import Decimal

from src.bfos.revenue_engine import get_revenue_summary


def summarize_daily_revenue() -> dict:
    return get_revenue_summary("24h")


def summarize_monthly_revenue() -> dict:
    return get_revenue_summary("30d")


def estimate_run_rate() -> dict:
    monthly = summarize_monthly_revenue()
    monthly_total = Decimal(monthly.get("total_amount", "0"))
    return {
        "monthly_total": str(monthly_total),
        "annualized_run_rate": str((monthly_total * Decimal("12")).quantize(Decimal("0.01"))),
    }
