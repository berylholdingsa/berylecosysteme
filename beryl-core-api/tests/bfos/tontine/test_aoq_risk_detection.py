from __future__ import annotations

from decimal import Decimal

from src.bfos.tontine.aoq_tontine_engine import (
    adjust_reputation,
    detect_collusion,
    detect_default_risk,
    detect_schedule_manipulation,
    freeze_group_if_needed,
)


def test_aoq_detects_default_risk_and_can_freeze_group() -> None:
    signal = detect_default_risk({"avg_reputation": "18", "missed_contributions": 2})
    assert signal["flagged"] is True
    assert signal["severity"] == "critical"

    next_status = freeze_group_if_needed("ACTIVE", [signal])
    assert next_status == "FROZEN"


def test_aoq_detects_schedule_manipulation_and_collusion_placeholders() -> None:
    schedule_signal = detect_schedule_manipulation(
        {
            "stored_frequency": "WEEKLY",
            "requested_frequency": "MONTHLY",
            "cycle_active": True,
        }
    )
    assert schedule_signal["flagged"] is True

    collusion_signal = detect_collusion({"duplicate_votes": 1, "rapid_multi_votes": 4})
    assert collusion_signal["flagged"] is True


def test_aoq_adjust_reputation_applies_penalty() -> None:
    updated = adjust_reputation(Decimal("50.00"), "fraud_attempt")
    assert updated < Decimal("50.00")
