"""Scheduling rules for Tontine cycles and frequency locking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.observability.logging.logger import logger


VALID_FREQUENCIES: dict[str, int] = {
    "DAILY": 1,
    "WEEKLY": 7,
    "BIWEEKLY": 14,
    "MONTHLY": 30,
}


def validate_frequency(frequency_type: str) -> str:
    """Validate and normalize Tontine distribution frequency."""
    normalized = frequency_type.strip().upper()
    if normalized not in VALID_FREQUENCIES:
        raise ValueError("frequency_type must be one of: DAILY, WEEKLY, BIWEEKLY, MONTHLY")
    return normalized


def calculate_next_distribution_date(
    frequency_type: str,
    *,
    from_date: datetime | None = None,
) -> datetime:
    """Compute next distribution date from a validated frequency."""
    normalized = validate_frequency(frequency_type)
    anchor = from_date or datetime.now(timezone.utc)
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    return anchor + timedelta(days=VALID_FREQUENCIES[normalized])


def enforce_schedule_lock(
    *,
    stored_frequency: str,
    requested_frequency: str,
    cycle_active: bool,
) -> None:
    """Reject frequency changes while a cycle is active."""
    current = validate_frequency(stored_frequency)
    requested = validate_frequency(requested_frequency)
    if cycle_active and current != requested:
        logger.warning(
            "event=tontine_schedule_lock_violation",
            stored_frequency=current,
            requested_frequency=requested,
        )
        raise ValueError("frequency_type is immutable during active cycle")
