"""Feature extraction for IAESG v1 heuristic scoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any, Iterable, Mapping

_MAX_DISTANCE_KM = 1000.0
_MAX_FUTURE_DRIFT = timedelta(minutes=5)
_MAX_PAST_DRIFT = timedelta(days=3650)
_DUPLICATE_DISTANCE_TOLERANCE_KM = 0.1
_DUPLICATE_WINDOW = timedelta(hours=24)


def extract_basic_features(impact_record) -> dict[str, Any]:
    """Extract first-order plausibility and integrity signals."""
    distance_km = _as_float(_read_value(impact_record, "distance_km"), default=0.0)
    thermal_factor_local = _as_float(_read_value(impact_record, "thermal_factor_local"), default=0.0)
    ev_factor_local = _as_float(_read_value(impact_record, "ev_factor_local"), default=0.0)
    country_code = str(_read_value(impact_record, "country_code", "")).upper()
    event_timestamp = _to_datetime(_read_value(impact_record, "event_timestamp"))
    now_utc = datetime.now(UTC)

    timestamp_coherence = False
    if event_timestamp is not None:
        timestamp_coherence = (now_utc - _MAX_PAST_DRIFT) <= event_timestamp <= (now_utc + _MAX_FUTURE_DRIFT)

    methodology_version = str(_read_value(impact_record, "methodology_version", "")).strip()
    model_version = str(_read_value(impact_record, "model_version", "")).strip()

    return {
        "distance_km": distance_km,
        "distance_plausible": 0.0 < distance_km <= _MAX_DISTANCE_KM,
        "country_code": country_code,
        "country_supported": len(country_code) == 2 and country_code.isalpha(),
        "country_factor_consistency": thermal_factor_local > ev_factor_local >= 0.0,
        "thermal_factor_local": thermal_factor_local,
        "ev_factor_local": ev_factor_local,
        "timestamp_coherence": timestamp_coherence,
        "event_timestamp": event_timestamp,
        "geo_hash": str(_read_value(impact_record, "geo_hash", "")),
        "methodology_consistency": bool(methodology_version or model_version),
        "crypto_integrity_ok": bool(_read_value(impact_record, "crypto_integrity_ok", True)),
    }


def extract_temporal_features(impact_record) -> dict[str, Any]:
    """Extract temporal consistency features from current/previous events."""
    distance_km = _as_float(_read_value(impact_record, "distance_km"), default=0.0)
    event_timestamp = _to_datetime(_read_value(impact_record, "event_timestamp"))
    previous_event_timestamp = _to_datetime(_read_value(impact_record, "previous_event_timestamp"))
    previous_distance_km = _as_float(_read_value(impact_record, "previous_distance_km"), default=0.0)
    recent_event_count = _as_int(_read_value(impact_record, "recent_event_count"), default=0)

    inferred_speed_kmh: float | None = None
    timestamp_order_consistent = True
    if event_timestamp is not None and previous_event_timestamp is not None:
        delta_seconds = (event_timestamp - previous_event_timestamp).total_seconds()
        timestamp_order_consistent = delta_seconds >= 0
        if delta_seconds > 0:
            inferred_speed_kmh = round(distance_km / (delta_seconds / 3600.0), 6)

    return {
        "inferred_speed_kmh": inferred_speed_kmh,
        "timestamp_order_consistent": timestamp_order_consistent,
        "recent_event_count": recent_event_count,
        "burst_detected": recent_event_count >= 4,
        "previous_distance_km": previous_distance_km,
    }


def extract_historical_features(impact_record, history: Iterable[object]) -> dict[str, Any]:
    """Extract historical drift/duplication features from prior records."""
    records = list(history)
    distance_km = _as_float(_read_value(impact_record, "distance_km"), default=0.0)
    event_timestamp = _to_datetime(_read_value(impact_record, "event_timestamp"))
    geo_hash = str(_read_value(impact_record, "geo_hash", ""))
    country_code = str(_read_value(impact_record, "country_code", "")).upper()

    distances: list[float] = []
    duplicate_similarity_count = 0

    for record in records:
        item_distance = _as_float(_read_value(record, "distance_km"), default=0.0)
        if item_distance > 0.0:
            distances.append(item_distance)

        item_geo_hash = str(_read_value(record, "geo_hash", ""))
        item_country_code = str(_read_value(record, "country_code", "")).upper()
        item_timestamp = _to_datetime(_read_value(record, "event_timestamp"))
        if item_geo_hash != geo_hash or item_country_code != country_code:
            continue
        if abs(item_distance - distance_km) > _DUPLICATE_DISTANCE_TOLERANCE_KM:
            continue
        if event_timestamp is not None and item_timestamp is not None:
            if abs(event_timestamp - item_timestamp) > _DUPLICATE_WINDOW:
                continue
        duplicate_similarity_count += 1

    historical_distance_avg = mean(distances) if distances else distance_km
    historical_distance_deviation = abs(distance_km - historical_distance_avg)
    if historical_distance_avg <= 0:
        historical_distance_deviation_ratio = 0.0
    else:
        historical_distance_deviation_ratio = historical_distance_deviation / historical_distance_avg

    return {
        "history_size": len(records),
        "historical_distance_avg_km": round(historical_distance_avg, 6),
        "historical_distance_deviation_km": round(historical_distance_deviation, 6),
        "historical_distance_deviation_ratio": round(historical_distance_deviation_ratio, 6),
        "duplicate_similarity_count": duplicate_similarity_count,
        "pattern_duplication": duplicate_similarity_count > 0,
    }


def _read_value(record: object, field_name: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(field_name, default)
    return getattr(record, field_name, default)


def _as_float(value: Any, *, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, str):
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None
