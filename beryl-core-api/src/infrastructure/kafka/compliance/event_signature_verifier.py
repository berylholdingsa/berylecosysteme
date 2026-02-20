"""Financial event signing and verification with HMAC."""

from __future__ import annotations

import json

from src.core.security.crypto import signature_service
from src.core.security.key_management import key_manager


class EventSignatureVerifier:
    def __init__(self) -> None:
        self._secret = key_manager.get_event_hmac_secret()

    def sign(self, payload: dict) -> str:
        return signature_service.sign(payload=payload, secret=self._secret)

    def attach_signature(self, payload: dict) -> dict:
        unsigned = dict(payload)
        signature = self.sign(unsigned)
        unsigned["signature"] = signature
        return unsigned

    def verify(self, payload: dict) -> bool:
        signature = payload.get("signature")
        if not signature:
            return False
        unsigned = dict(payload)
        unsigned.pop("signature", None)
        return signature_service.verify(payload=unsigned, signature=signature, secret=self._secret)

    def canonical_payload(self, payload: dict) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


event_signature_verifier = EventSignatureVerifier()
