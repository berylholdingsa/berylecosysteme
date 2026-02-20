"""Deterministic IAESG scoring heuristics."""

from __future__ import annotations

from typing import Any

_MAX_SCORE = 100
_MIN_SCORE = 0
_SPEED_WARNING_KMH = 130.0
_SPEED_CRITICAL_KMH = 180.0


def compute_confidence_score(features: dict[str, Any]) -> int:
    """Compute a confidence score in [0, 100] from heuristic signals."""
    score = 0

    score += 20 if _as_bool(features.get("distance_plausible")) else -40
    score += 10 if _as_bool(features.get("country_factor_consistency")) else -15
    score += 10 if _as_bool(features.get("timestamp_coherence")) else -20
    score += 5 if _as_bool(features.get("timestamp_order_consistent", True)) else -10
    score += 5 if _as_bool(features.get("country_supported", True)) else -10
    score += 5 if _as_bool(features.get("methodology_consistency", True)) else -20

    speed = _as_optional_float(features.get("inferred_speed_kmh"))
    if speed is None:
        score += 5
    elif 0.0 <= speed <= _SPEED_WARNING_KMH:
        score += 10
    elif speed <= _SPEED_CRITICAL_KMH:
        score -= 15
    else:
        score -= 30

    score += -20 if _as_bool(features.get("burst_detected")) else 5
    score += -20 if _as_bool(features.get("pattern_duplication")) else 5

    drift_ratio = _as_optional_float(features.get("historical_distance_deviation_ratio")) or 0.0
    if drift_ratio <= 1.0:
        score += 5
    elif drift_ratio > 3.0:
        score -= 10

    score += 30 if _as_bool(features.get("crypto_integrity_ok", True)) else -50
    return _clamp(score)


def compute_integrity_index(features: dict[str, Any]) -> int:
    """Compute data integrity index in [0, 100], weighted toward cryptographic integrity."""
    index = 0
    index += 40 if _as_bool(features.get("crypto_integrity_ok", True)) else 0
    index += 20 if _as_bool(features.get("methodology_consistency", True)) else 0
    index += 15 if _as_bool(features.get("timestamp_coherence")) else 0
    index += 15 if _as_bool(features.get("country_factor_consistency")) else 0
    index += 10 if _as_bool(features.get("distance_plausible")) else 0

    if _as_bool(features.get("pattern_duplication")) or _as_bool(features.get("burst_detected")):
        index -= 15

    speed = _as_optional_float(features.get("inferred_speed_kmh"))
    if speed is not None:
        if speed > _SPEED_CRITICAL_KMH:
            index -= 20
        elif speed > _SPEED_WARNING_KMH:
            index -= 10

    return _clamp(index)


def _as_bool(value: Any) -> bool:
    return bool(value)


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: int) -> int:
    return max(_MIN_SCORE, min(_MAX_SCORE, int(round(value))))
