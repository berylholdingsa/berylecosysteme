"""Strict canonical JSON utilities for MRV hashing stability."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping


_FLOAT_QUANT = Decimal("0.000000")


def canonical_json_strict(payload: Mapping[str, Any]) -> str:
    """Serialize payload with deterministic key order and numeric normalization."""
    normalized = _normalize(payload)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex_strict(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash over canonical strict JSON."""
    canonical = canonical_json_strict(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(value[key]) for key in sorted(value.keys(), key=lambda item: str(item))}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, Decimal):
        return _normalize_decimal(value)
    if isinstance(value, float):
        return _normalize_decimal(Decimal(str(value)))
    return value


def _normalize_decimal(value: Decimal) -> str:
    quantized = value.quantize(_FLOAT_QUANT, rounding=ROUND_HALF_UP)
    rendered = format(quantized, "f")
    rendered = rendered.rstrip("0").rstrip(".")
    if rendered in {"", "-0"}:
        return "0"
    return rendered

