"""GreenOS cryptographic signing utilities (HMAC-SHA256 + Ed25519)."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from src.config.settings import settings
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.secrets import (
    GREENOS_REQUIRED_SIGNING_SECRETS,
    SECRET_GREENOS_ED25519_ACTIVE_KEY_VERSION,
    SECRET_GREENOS_ED25519_PRIVATE_KEY,
    SECRET_GREENOS_ED25519_PRIVATE_KEYS_JSON,
    SECRET_GREENOS_ED25519_PUBLIC_KEY,
    SECRET_GREENOS_ED25519_PUBLIC_KEYS_JSON,
    SECRET_GREENOS_SIGNING_ACTIVE_KEY_VERSION,
    SECRET_GREENOS_SIGNING_KEYS_JSON,
    SECRET_GREENOS_SIGNING_SECRET,
    SecretMissingError,
    SecretProvider,
    SecretProviderError,
    build_secret_provider,
)


SIGNATURE_ALGORITHM_HMAC_SHA256 = "HMAC-SHA256"
SIGNATURE_ALGORITHM_ED25519 = "ED25519"
PUBLIC_KEY_ENCODING_BASE64 = "base64"
DEFAULT_GREENOS_HMAC_SECRET = "change-me-greenos-signing-secret"
DEFAULT_GREENOS_ED25519_PRIVATE_KEY = "y4RvmUHSyyFmAuuIL8g17LxPYLj/Kti53WN8bNyl4XU="
DEFAULT_GREENOS_ED25519_PUBLIC_KEY = "mVoiTw3s4D07BzqO1aE6IN4x+lfUzKhXjgPX0W03GL8="
PRODUCTION_ENV_NAMES = {"production", "prod"}


@dataclass(frozen=True)
class SignatureResult:
    """Signature envelope persisted with immutable records."""

    signature: str
    signature_algorithm: str
    key_version: str


@dataclass(frozen=True)
class PublicKeyResult:
    """Public key envelope for independent third-party verification."""

    public_key: str
    fingerprint_sha256: str
    signature_algorithm: str
    key_version: str
    encoding: str = PUBLIC_KEY_ENCODING_BASE64


class GreenOSSignatureService:
    """HMAC and Ed25519 signer/verifier with key-version support."""

    def __init__(
        self,
        *,
        active_key_version: str | None = None,
        active_secret: str | None = None,
        keyring: dict[str, str] | None = None,
        asym_active_key_version: str | None = None,
        asym_private_key: str | None = None,
        asym_public_key: str | None = None,
        asym_private_keyring: dict[str, str] | None = None,
        asym_public_keyring: dict[str, str] | None = None,
        secret_provider: SecretProvider | None = None,
    ) -> None:
        self._active_key_version_override = active_key_version
        self._active_secret_override = active_secret
        self._keyring_override = dict(keyring) if keyring is not None else None
        self._asym_active_key_version_override = asym_active_key_version
        self._asym_private_key_override = asym_private_key
        self._asym_public_key_override = asym_public_key
        self._asym_private_keyring_override = (
            dict(asym_private_keyring) if asym_private_keyring is not None else None
        )
        self._asym_public_keyring_override = (
            dict(asym_public_keyring) if asym_public_keyring is not None else None
        )
        self._secret_provider = secret_provider or build_secret_provider()
        self._validate_production_signing_configuration()

    def sign_hash(self, hash_value: str) -> SignatureResult:
        keyring, active_key_version = self._resolve_keyring()
        secret = keyring.get(active_key_version) or self._resolve_active_secret()
        if not secret:
            raise RuntimeError("GREENOS_SIGNING_SECRET configuration is missing for active key version")
        signature = _hmac_sha256_hex(secret=secret, value=hash_value)
        return SignatureResult(
            signature=signature,
            signature_algorithm=SIGNATURE_ALGORITHM_HMAC_SHA256,
            key_version=active_key_version,
        )

    def verify_hash_signature(
        self,
        *,
        hash_value: str,
        signature: str | None,
        signature_algorithm: str | None,
        key_version: str | None,
    ) -> bool:
        if not signature:
            return False
        if signature_algorithm != SIGNATURE_ALGORITHM_HMAC_SHA256:
            return False

        keyring, _active_key_version = self._resolve_keyring()
        candidate_secrets: list[str] = []

        if key_version and key_version in keyring:
            candidate_secrets.append(keyring[key_version])
        for secret in keyring.values():
            if secret not in candidate_secrets:
                candidate_secrets.append(secret)
        if not candidate_secrets:
            candidate_secrets.append(self._resolve_active_secret())

        for secret in candidate_secrets:
            expected = _hmac_sha256_hex(secret=secret, value=hash_value)
            if hmac.compare_digest(expected, signature):
                return True
        return False

    def sign_hash_asymmetric(self, hash_value: str) -> SignatureResult:
        private_keyring, _public_keyring, active_key_version = self._resolve_asymmetric_keyrings()
        private_material = private_keyring.get(active_key_version)
        private_key = self._private_key_from_material(private_material) if private_material else None
        if private_key is None:
            raise RuntimeError(
                "GREENOS_ED25519_PRIVATE_KEY configuration is missing or invalid for active key version"
            )

        raw_signature = private_key.sign(hash_value.encode("utf-8"))
        signature = base64.b64encode(raw_signature).decode("ascii")
        return SignatureResult(
            signature=signature,
            signature_algorithm=SIGNATURE_ALGORITHM_ED25519,
            key_version=active_key_version,
        )

    def verify_hash_asymmetric_signature(
        self,
        *,
        hash_value: str,
        signature: str | None,
        signature_algorithm: str | None,
        key_version: str | None,
    ) -> bool:
        if not signature:
            return False
        if signature_algorithm != SIGNATURE_ALGORITHM_ED25519:
            return False

        signature_bytes = self._signature_from_base64(signature)
        if signature_bytes is None:
            return False

        _private_keyring, public_keyring, _active_key_version = self._resolve_asymmetric_keyrings()
        candidate_public_materials: list[str] = []

        if key_version and key_version in public_keyring:
            candidate_public_materials.append(public_keyring[key_version])
        for material in public_keyring.values():
            if material not in candidate_public_materials:
                candidate_public_materials.append(material)

        for material in candidate_public_materials:
            public_key = self._public_key_from_material(material)
            if public_key is None:
                continue
            try:
                public_key.verify(signature_bytes, hash_value.encode("utf-8"))
                return True
            except InvalidSignature:
                continue
        return False

    @classmethod
    def verify_hash_with_public_key(
        cls,
        *,
        hash_value: str,
        signature: str | None,
        public_key: str | None,
    ) -> bool:
        if not signature or not public_key:
            return False
        signature_bytes = cls._signature_from_base64(signature)
        if signature_bytes is None:
            return False
        parsed_public_key = cls._public_key_from_material(public_key)
        if parsed_public_key is None:
            return False
        try:
            parsed_public_key.verify(signature_bytes, hash_value.encode("utf-8"))
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def generate_ed25519_keypair() -> tuple[str, str]:
        """Generate a raw Ed25519 keypair encoded in base64."""
        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return (
            base64.b64encode(private_bytes).decode("ascii"),
            base64.b64encode(public_bytes).decode("ascii"),
        )

    def get_public_key(self, *, key_version: str | None = None) -> PublicKeyResult:
        private_keyring, public_keyring, active_key_version = self._resolve_asymmetric_keyrings()
        resolved_key_version = key_version or active_key_version
        public_material = public_keyring.get(resolved_key_version)

        if public_material is None:
            private_material = private_keyring.get(resolved_key_version)
            if private_material is not None:
                public_material = self._derive_public_key_from_private_material(private_material)

        normalized_public_key = self._normalize_public_key_material(public_material)
        if normalized_public_key is None:
            raise ValueError(f"No Ed25519 public key found for key_version={resolved_key_version}")

        public_bytes = self._decode_base64_bytes(normalized_public_key)
        if public_bytes is None:
            raise ValueError(f"Invalid Ed25519 public key format for key_version={resolved_key_version}")

        return PublicKeyResult(
            public_key=normalized_public_key,
            fingerprint_sha256=self._sha256_hex(public_bytes),
            signature_algorithm=SIGNATURE_ALGORITHM_ED25519,
            key_version=resolved_key_version,
        )

    @property
    def secret_provider_name(self) -> str:
        return self._secret_provider.provider_name

    @property
    def secret_provider_cache_ttl_seconds(self) -> float:
        return self._secret_provider.cache_ttl_seconds

    def secret_status_snapshot(self) -> dict[str, object]:
        statuses = {name: self._status_for_secret_name(name=name) for name in GREENOS_REQUIRED_SIGNING_SECRETS}
        return {
            "provider": self.secret_provider_name,
            "checked_at": datetime.now(UTC),
            "statuses": statuses,
        }

    def _status_for_secret_name(self, *, name: str) -> str:
        try:
            raw = self._secret_provider.get_secret(name)
        except SecretMissingError:
            return "MISSING"
        except SecretProviderError:
            return "INVALID"

        if not raw.strip():
            return "MISSING"

        if name == SECRET_GREENOS_SIGNING_SECRET and raw == DEFAULT_GREENOS_HMAC_SECRET:
            return "INVALID"
        if name == SECRET_GREENOS_ED25519_PRIVATE_KEY:
            if raw == DEFAULT_GREENOS_ED25519_PRIVATE_KEY:
                return "INVALID"
            return "OK" if self._private_key_from_material(raw) is not None else "INVALID"
        if name == SECRET_GREENOS_ED25519_PUBLIC_KEY:
            if raw == DEFAULT_GREENOS_ED25519_PUBLIC_KEY:
                return "INVALID"
            return "OK" if self._public_key_from_material(raw) is not None else "INVALID"
        if name in {
            SECRET_GREENOS_SIGNING_KEYS_JSON,
            SECRET_GREENOS_ED25519_PRIVATE_KEYS_JSON,
            SECRET_GREENOS_ED25519_PUBLIC_KEYS_JSON,
        }:
            parsed = self._parse_key_map(raw)
            if raw.strip() in {"{}", ""}:
                return "OK"
            return "OK" if parsed else "INVALID"
        return "OK"

    def _validate_production_signing_configuration(self) -> None:
        if settings.environment.strip().lower() not in PRODUCTION_ENV_NAMES:
            return

        if self.secret_provider_name != "env":
            for secret_name in GREENOS_REQUIRED_SIGNING_SECRETS:
                try:
                    self._secret_provider.get_secret(secret_name)
                except SecretProviderError as exc:
                    raise RuntimeError(
                        f"GreenOS secret provider '{self.secret_provider_name}' is not ready in production: {secret_name}"
                    ) from exc

        keyring, active_hmac_key_version = self._resolve_keyring()
        hmac_secret = keyring.get(active_hmac_key_version) or self._resolve_active_secret()
        if not hmac_secret or hmac_secret == DEFAULT_GREENOS_HMAC_SECRET:
            raise RuntimeError(
                "GreenOS HMAC signing secret is missing or placeholder in production environment"
            )

        private_keyring, public_keyring, active_asym_key_version = self._resolve_asymmetric_keyrings()
        private_material = private_keyring.get(active_asym_key_version)
        public_material = public_keyring.get(active_asym_key_version)
        if not private_material:
            raise RuntimeError(
                "GreenOS Ed25519 private key is missing for active key version in production environment"
            )
        if private_material == DEFAULT_GREENOS_ED25519_PRIVATE_KEY:
            raise RuntimeError("GreenOS Ed25519 private key placeholder cannot be used in production")
        if self._private_key_from_material(private_material) is None:
            raise RuntimeError("GreenOS Ed25519 private key is invalid in production environment")

        if public_material is None:
            public_material = self._derive_public_key_from_private_material(private_material)
        if not public_material:
            raise RuntimeError(
                "GreenOS Ed25519 public key is missing for active key version in production environment"
            )
        if public_material == DEFAULT_GREENOS_ED25519_PUBLIC_KEY:
            raise RuntimeError("GreenOS Ed25519 public key placeholder cannot be used in production")
        if self._public_key_from_material(public_material) is None:
            raise RuntimeError("GreenOS Ed25519 public key is invalid in production environment")

    def _resolve_keyring(self) -> tuple[dict[str, str], str]:
        active_key_version = self._resolve_hmac_active_key_version()
        active_secret = self._resolve_active_secret()
        keyring = (
            self._load_hmac_keyring_from_secret_provider()
            if self._keyring_override is None
            else dict(self._keyring_override)
        )
        if active_secret:
            keyring[active_key_version] = active_secret
        return keyring, active_key_version

    def _resolve_asymmetric_keyrings(self) -> tuple[dict[str, str], dict[str, str], str]:
        active_key_version = self._resolve_asymmetric_active_key_version()
        private_keyring = (
            self._load_asymmetric_private_keyring_from_secret_provider()
            if self._asym_private_keyring_override is None
            else dict(self._asym_private_keyring_override)
        )
        public_keyring = (
            self._load_asymmetric_public_keyring_from_secret_provider()
            if self._asym_public_keyring_override is None
            else dict(self._asym_public_keyring_override)
        )

        active_private_key = self._resolve_asymmetric_active_private_key()
        if active_private_key:
            private_keyring[active_key_version] = active_private_key

        active_public_key = self._resolve_asymmetric_active_public_key()
        if active_public_key:
            public_keyring[active_key_version] = active_public_key

        for version, private_material in private_keyring.items():
            if version in public_keyring:
                continue
            derived_public = self._derive_public_key_from_private_material(private_material)
            if derived_public is not None:
                public_keyring[version] = derived_public

        return private_keyring, public_keyring, active_key_version

    def _resolve_active_secret(self) -> str:
        if self._active_secret_override is not None:
            return self._active_secret_override
        return self._read_secret(
            secret_name=SECRET_GREENOS_SIGNING_SECRET,
            fallback=settings.greenos_signing_secret,
        )

    def _resolve_hmac_active_key_version(self) -> str:
        if self._active_key_version_override is not None:
            return self._active_key_version_override
        active_key_version = self._read_secret(
            secret_name=SECRET_GREENOS_SIGNING_ACTIVE_KEY_VERSION,
            fallback=settings.greenos_signing_active_key_version,
        )
        return active_key_version or "v1"

    def _resolve_asymmetric_active_private_key(self) -> str:
        if self._asym_private_key_override is not None:
            return self._asym_private_key_override
        return self._read_secret(
            secret_name=SECRET_GREENOS_ED25519_PRIVATE_KEY,
            fallback=settings.greenos_ed25519_private_key,
        )

    def _resolve_asymmetric_active_public_key(self) -> str:
        if self._asym_public_key_override is not None:
            return self._asym_public_key_override
        return self._read_secret(
            secret_name=SECRET_GREENOS_ED25519_PUBLIC_KEY,
            fallback=settings.greenos_ed25519_public_key,
        )

    def _resolve_asymmetric_active_key_version(self) -> str:
        if self._asym_active_key_version_override is not None:
            return self._asym_active_key_version_override
        active_key_version = self._read_secret(
            secret_name=SECRET_GREENOS_ED25519_ACTIVE_KEY_VERSION,
            fallback=settings.greenos_ed25519_active_key_version,
        )
        return active_key_version or "v1"

    def _load_hmac_keyring_from_secret_provider(self) -> dict[str, str]:
        raw = self._read_secret(
            secret_name=SECRET_GREENOS_SIGNING_KEYS_JSON,
            fallback=settings.greenos_signing_keys_json,
        )
        return self._parse_key_map(raw)

    def _load_asymmetric_private_keyring_from_secret_provider(self) -> dict[str, str]:
        raw = self._read_secret(
            secret_name=SECRET_GREENOS_ED25519_PRIVATE_KEYS_JSON,
            fallback=settings.greenos_ed25519_private_keys_json,
        )
        return self._parse_key_map(raw)

    def _load_asymmetric_public_keyring_from_secret_provider(self) -> dict[str, str]:
        raw = self._read_secret(
            secret_name=SECRET_GREENOS_ED25519_PUBLIC_KEYS_JSON,
            fallback=settings.greenos_ed25519_public_keys_json,
        )
        return self._parse_key_map(raw)

    def _read_secret(self, *, secret_name: str, fallback: str) -> str:
        try:
            return self._secret_provider.get_secret(secret_name)
        except SecretMissingError:
            return fallback
        except SecretProviderError as exc:
            logger.warning(
                "event=greenos_secret_provider_read_failed",
                provider=self.secret_provider_name,
                secret_name=secret_name,
                error_type=type(exc).__name__,
            )
            return fallback

    @staticmethod
    def _parse_key_map(raw: str) -> dict[str, str]:
        if not raw:
            return {}
        try:
            parsed: Any = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        keyring: dict[str, str] = {}
        for key_version, value in parsed.items():
            if isinstance(key_version, str) and isinstance(value, str) and key_version and value:
                keyring[key_version] = value
        return keyring

    @staticmethod
    def _private_key_from_material(material: str | None) -> Ed25519PrivateKey | None:
        if not material:
            return None
        normalized = material.strip()
        if not normalized:
            return None

        if "BEGIN" in normalized:
            try:
                key = serialization.load_pem_private_key(normalized.encode("utf-8"), password=None)
            except (TypeError, ValueError):
                return None
            if isinstance(key, Ed25519PrivateKey):
                return key
            return None

        raw = GreenOSSignatureService._decode_base64_bytes(normalized)
        if raw is None:
            return None
        if len(raw) == 64:
            raw = raw[:32]
        if len(raw) != 32:
            return None
        try:
            return Ed25519PrivateKey.from_private_bytes(raw)
        except ValueError:
            return None

    @staticmethod
    def _public_key_from_material(material: str | None) -> Ed25519PublicKey | None:
        if not material:
            return None
        normalized = material.strip()
        if not normalized:
            return None

        if "BEGIN" in normalized:
            try:
                key = serialization.load_pem_public_key(normalized.encode("utf-8"))
            except ValueError:
                return None
            if isinstance(key, Ed25519PublicKey):
                return key
            return None

        raw = GreenOSSignatureService._decode_base64_bytes(normalized)
        if raw is None or len(raw) != 32:
            return None
        try:
            return Ed25519PublicKey.from_public_bytes(raw)
        except ValueError:
            return None

    @staticmethod
    def _normalize_public_key_material(material: str | None) -> str | None:
        public_key = GreenOSSignatureService._public_key_from_material(material)
        if public_key is None:
            return None
        raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def _derive_public_key_from_private_material(material: str | None) -> str | None:
        private_key = GreenOSSignatureService._private_key_from_material(material)
        if private_key is None:
            return None
        raw = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def _signature_from_base64(signature: str | None) -> bytes | None:
        if not signature:
            return None
        try:
            return base64.b64decode(signature.encode("ascii"), validate=True)
        except (ValueError, binascii.Error):
            return None

    @staticmethod
    def _decode_base64_bytes(value: str) -> bytes | None:
        try:
            return base64.b64decode(value.encode("ascii"), validate=True)
        except (ValueError, binascii.Error):
            return None

    @staticmethod
    def _sha256_hex(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()


def _hmac_sha256_hex(*, secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), "sha256").hexdigest()
