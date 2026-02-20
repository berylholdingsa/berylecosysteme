"""Reasoning summary builder for IAESG decisions."""

from __future__ import annotations

from typing import Any


def build_reasoning_summary(
    *,
    features: dict[str, Any],
    confidence_score: int,
    integrity_index: int,
    anomaly_flags: list[str],
    aoq_status: str,
) -> dict[str, Any]:
    """Return deterministic machine-readable reasoning for audits."""
    summary_parts: list[str] = []
    if anomaly_flags:
        summary_parts.append("anomalies_detected")
    if bool(features.get("distance_plausible")):
        summary_parts.append("distance_plausible")
    else:
        summary_parts.append("distance_implausible")
    if bool(features.get("crypto_integrity_ok", True)):
        summary_parts.append("crypto_integrity_ok")
    else:
        summary_parts.append("crypto_integrity_failure")

    return {
        "summary": ",".join(summary_parts),
        "confidence_score": int(confidence_score),
        "integrity_index": int(integrity_index),
        "aoq_status": str(aoq_status),
        "signals": {
            "distance_km": _as_optional_float(features.get("distance_km")),
            "inferred_speed_kmh": _as_optional_float(features.get("inferred_speed_kmh")),
            "historical_distance_deviation_ratio": _as_optional_float(
                features.get("historical_distance_deviation_ratio")
            ),
            "recent_event_count": _as_optional_int(features.get("recent_event_count")),
            "duplicate_similarity_count": _as_optional_int(features.get("duplicate_similarity_count")),
            "country_factor_consistency": bool(features.get("country_factor_consistency")),
            "timestamp_coherence": bool(features.get("timestamp_coherence")),
            "methodology_consistency": bool(features.get("methodology_consistency", True)),
            "crypto_integrity_ok": bool(features.get("crypto_integrity_ok", True)),
        },
        "anomaly_flags": list(anomaly_flags),
    }


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
