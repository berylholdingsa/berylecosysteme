"""AOQ hooks for BTSE risk detection and freeze decisions."""

from __future__ import annotations

from decimal import Decimal

from src.bfos.tontine.reputation_engine import reputation_engine
from src.observability.logging.logger import logger


def detect_collusion(context: dict | None = None) -> dict:
    """Detect suspicious coordinated voting behavior."""
    payload = context or {}
    duplicate_votes = int(payload.get("duplicate_votes", 0))
    rapid_multi_votes = int(payload.get("rapid_multi_votes", 0))
    flagged = duplicate_votes > 0 or rapid_multi_votes > 3
    severity = "critical" if rapid_multi_votes > 5 else ("high" if flagged else "low")
    result = {
        "signal": "collusion",
        "flagged": flagged,
        "severity": severity,
        "reason": "aoq_tontine_collusion_heuristic",
    }
    logger.info("event=tontine_aoq_collusion_evaluated", result=str(result))
    return result


def detect_default_risk(context: dict | None = None) -> dict:
    """Detect elevated default risk from contribution/reputation indicators."""
    payload = context or {}
    missed_contributions = int(payload.get("missed_contributions", 0))
    avg_reputation = Decimal(str(payload.get("avg_reputation", "50")))
    flagged = missed_contributions > 0 or avg_reputation < Decimal("30")
    severity = "critical" if avg_reputation < Decimal("20") else ("high" if flagged else "low")
    result = {
        "signal": "default_risk",
        "flagged": flagged,
        "severity": severity,
        "reason": "aoq_tontine_default_risk_heuristic",
    }
    logger.info("event=tontine_aoq_default_risk_evaluated", result=str(result))
    return result


def detect_schedule_manipulation(context: dict | None = None) -> dict:
    """Detect active-cycle frequency tampering attempts."""
    payload = context or {}
    stored_frequency = str(payload.get("stored_frequency", "")).upper()
    requested_frequency = str(payload.get("requested_frequency", "")).upper()
    cycle_active = bool(payload.get("cycle_active", False))
    flagged = cycle_active and stored_frequency != requested_frequency
    result = {
        "signal": "schedule_manipulation",
        "flagged": flagged,
        "severity": "critical" if flagged else "low",
        "reason": "aoq_tontine_schedule_lock_enforcement",
    }
    logger.info("event=tontine_aoq_schedule_evaluated", result=str(result))
    return result


def adjust_reputation(current_score: Decimal, event_type: str) -> Decimal:
    """Apply reputation adjustment through AOQ hook abstraction."""
    return reputation_engine.adjust_reputation(current_score=Decimal(str(current_score)), event_type=event_type)


def freeze_group_if_needed(current_status: str, signals: list[dict]) -> str:
    """Freeze group when any critical signal is raised."""
    if current_status == "FROZEN":
        return current_status
    critical = any(bool(signal.get("flagged")) and signal.get("severity") == "critical" for signal in signals)
    next_status = "FROZEN" if critical else current_status
    logger.info(
        "event=tontine_aoq_freeze_decision",
        current_status=current_status,
        next_status=next_status,
        critical=str(critical),
    )
    return next_status
