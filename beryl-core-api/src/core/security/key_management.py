"""Strict key management for security-sensitive operations."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from src.config.settings import settings
from src.observability.logging.logger import logger


class SecurityConfigurationError(RuntimeError):
    """Raised when security key configuration is invalid."""


@dataclass(frozen=True)
class SigningKey:
    kid: str
    secret: str
    created_at: datetime


class KeyManager:
    """Loads and validates runtime cryptographic material."""

    def __init__(self) -> None:
        self._signing_keys = self._load_signing_keys()

    def _load_signing_keys(self) -> dict[str, SigningKey]:
        raw = settings.jwt_signing_keys_json.strip()
        now = datetime.now(timezone.utc)

        if raw:
            try:
                decoded = json.loads(raw)
                if not isinstance(decoded, dict):
                    raise SecurityConfigurationError("JWT_SIGNING_KEYS_JSON must be a JSON object")
                keys = {
                    str(kid): SigningKey(kid=str(kid), secret=str(secret), created_at=now)
                    for kid, secret in decoded.items()
                    if str(secret).strip()
                }
                if not keys:
                    raise SecurityConfigurationError("JWT_SIGNING_KEYS_JSON cannot be empty")
                return keys
            except json.JSONDecodeError as exc:
                raise SecurityConfigurationError("Invalid JWT_SIGNING_KEYS_JSON format") from exc

        default_secret = settings.jwt_secret_key.strip()
        if not default_secret:
            raise SecurityConfigurationError("JWT secret key is missing")
        return {
            settings.jwt_active_kid: SigningKey(
                kid=settings.jwt_active_kid,
                secret=default_secret,
                created_at=now,
            )
        }

    def get_signing_keys(self) -> dict[str, SigningKey]:
        return dict(self._signing_keys)

    def get_active_signing_key(self) -> SigningKey:
        active = self._signing_keys.get(settings.jwt_active_kid)
        if active is not None:
            return active

        first_key = next(iter(self._signing_keys.values()))
        logger.warning(
            "event=security_active_kid_fallback configured_active_kid=%s fallback_kid=%s",
            settings.jwt_active_kid,
            first_key.kid,
        )
        return first_key

    def get_aes256_key(self) -> bytes:
        raw = settings.aes256_key_b64.strip()
        if raw:
            decoded = base64.b64decode(raw)
            if len(decoded) != 32:
                raise SecurityConfigurationError("AES256 key must decode to exactly 32 bytes")
            return decoded

        if settings.environment.lower() in {"development", "dev", "test"}:
            digest = hashlib.sha256(settings.audit_secret_key.encode("utf-8")).digest()
            logger.warning(f"event=security_aes_key_fallback environment={settings.environment}")
            return digest

        raise SecurityConfigurationError("AES256_KEY_B64 is required outside development/test")

    def get_event_hmac_secret(self) -> str:
        secret = settings.event_hmac_secret.strip()
        if not secret:
            raise SecurityConfigurationError("EVENT_HMAC_SECRET is required")
        return secret

    def get_psp_webhook_secret(self) -> str:
        secret = settings.psp_webhook_hmac_secret.strip()
        if not secret:
            raise SecurityConfigurationError("PSP_WEBHOOK_HMAC_SECRET is required")
        return secret

    def validate_runtime_security(self) -> None:
        env = settings.environment.lower()
        weak_defaults = {
            "change-me-jwt-secret",
            "change-me-event-hmac",
            "change-me-psp-hmac",
            "change-me-audit-hmac",
        }

        candidates = {
            settings.jwt_secret_key,
            settings.event_hmac_secret,
            settings.psp_webhook_hmac_secret,
            settings.audit_secret_key,
        }

        if env not in {"development", "dev", "test"} and candidates.intersection(weak_defaults):
            raise SecurityConfigurationError("Weak default secrets are not allowed in this environment")

    def generate_key_material(self, length: int = 64) -> str:
        return secrets.token_urlsafe(length)


key_manager = KeyManager()
