"""Ensures payload integrity with deterministic SHA-256 hashes."""

from __future__ import annotations

import hashlib
import json


class MessageIntegrityValidator:
    @staticmethod
    def compute_payload_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def enrich_with_hash(self, payload: dict) -> dict:
        enriched = dict(payload)
        enriched["payload_hash"] = self.compute_payload_hash(payload)
        return enriched

    def verify_hash(self, payload: dict) -> bool:
        expected = payload.get("payload_hash")
        if not expected:
            return False
        data = dict(payload)
        data.pop("payload_hash", None)
        actual = self.compute_payload_hash(data)
        return expected == actual
