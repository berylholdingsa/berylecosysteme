"""IAESG anomaly flagging heuristics."""

from __future__ import annotations

from typing import Any

ANOMALY_DISTANCE_IMPLAUSIBLE = "DISTANCE_IMPLAUSIBLE"
ANOMALY_SPEED_OUT_OF_RANGE = "SPEED_OUT_OF_RANGE"
ANOMALY_PATTERN_DUPLICATION = "PATTERN_DUPLICATION"
ANOMALY_METHODOLOGY_INCONSISTENCE = "METHODOLOGY_INCONSISTENCE"
ANOMALY_CRYPTO_INTEGRITY_FAILURE = "CRYPTO_INTEGRITY_FAILURE"

_SPEED_CRITICAL_KMH = 180.0


def detect_anomalies(features: dict[str, Any]) -> list[str]:
    """Detect anomaly flags from extracted IAESG features."""
    flags: set[str] = set()

    if not bool(features.get("distance_plausible")):
        flags.add(ANOMALY_DISTANCE_IMPLAUSIBLE)

    speed = _as_optional_float(features.get("inferred_speed_kmh"))
    if speed is not None and (speed < 0.0 or speed > _SPEED_CRITICAL_KMH):
        flags.add(ANOMALY_SPEED_OUT_OF_RANGE)

    if bool(features.get("pattern_duplication")) or bool(features.get("burst_detected")):
        flags.add(ANOMALY_PATTERN_DUPLICATION)

    if (
        not bool(features.get("methodology_consistency", True))
        or not bool(features.get("country_factor_consistency", True))
        or not bool(features.get("country_supported", True))
    ):
        flags.add(ANOMALY_METHODOLOGY_INCONSISTENCE)

    if not bool(features.get("crypto_integrity_ok", True)):
        flags.add(ANOMALY_CRYPTO_INTEGRITY_FAILURE)

    return sorted(flags)


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
