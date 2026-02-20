"""Hashing utilities for deterministic GreenOS payloads."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Serialize payload with deterministic key ordering."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: Mapping[str, Any]) -> str:
    """SHA256 hex digest over canonical JSON payload."""
    canonical = canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

