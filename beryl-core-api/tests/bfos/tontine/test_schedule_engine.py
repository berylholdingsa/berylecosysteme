from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.bfos.tontine.schedule_engine import (
    calculate_next_distribution_date,
    enforce_schedule_lock,
    validate_frequency,
)


def test_validate_frequency_accepts_only_supported_values() -> None:
    assert validate_frequency("daily") == "DAILY"
    assert validate_frequency("WEEKLY") == "WEEKLY"
    assert validate_frequency("biweekly") == "BIWEEKLY"
    assert validate_frequency("monthly") == "MONTHLY"

    with pytest.raises(ValueError):
        validate_frequency("YEARLY")


def test_calculate_next_distribution_date_from_fixed_anchor() -> None:
    anchor = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    next_daily = calculate_next_distribution_date("DAILY", from_date=anchor)
    next_weekly = calculate_next_distribution_date("WEEKLY", from_date=anchor)
    next_biweekly = calculate_next_distribution_date("BIWEEKLY", from_date=anchor)
    next_monthly = calculate_next_distribution_date("MONTHLY", from_date=anchor)

    assert (next_daily - anchor).days == 1
    assert (next_weekly - anchor).days == 7
    assert (next_biweekly - anchor).days == 14
    assert (next_monthly - anchor).days == 30


def test_enforce_schedule_lock_rejects_active_cycle_frequency_change() -> None:
    enforce_schedule_lock(stored_frequency="WEEKLY", requested_frequency="WEEKLY", cycle_active=True)

    with pytest.raises(ValueError, match="immutable"):
        enforce_schedule_lock(stored_frequency="WEEKLY", requested_frequency="MONTHLY", cycle_active=True)

    enforce_schedule_lock(stored_frequency="WEEKLY", requested_frequency="MONTHLY", cycle_active=False)
