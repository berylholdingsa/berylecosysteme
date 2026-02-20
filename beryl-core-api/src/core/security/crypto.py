"""Cryptographic primitives for password hashing and sensitive data encryption."""

from __future__ import annotations

import base64
import hmac
import json
import secrets
from hashlib import sha256

from src.config.settings import settings
from src.core.security.key_management import key_manager

try:
    from passlib.context import CryptContext
except ModuleNotFoundError:  # pragma: no cover - runtime dependency guard
    CryptContext = None

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ModuleNotFoundError:  # pragma: no cover - runtime dependency guard
    AESGCM = None


if CryptContext is not None:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=max(12, settings.bcrypt_rounds),
    )
else:
    pwd_context = None


class PasswordHasher:
    @staticmethod
    def hash_password(password: str) -> str:
        if pwd_context is None:
            return "sha256$" + sha256(password.encode("utf-8")).hexdigest()
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        if pwd_context is None:
            return hashed_password == ("sha256$" + sha256(password.encode("utf-8")).hexdigest())
        return pwd_context.verify(password, hashed_password)


class Aes256Cipher:
    """AES-256-GCM envelope encryption for sensitive application payloads."""

    def __init__(self) -> None:
        self._key = key_manager.get_aes256_key()
        self._available = AESGCM is not None

    def encrypt_json(self, payload: dict) -> str:
        if not self._available:
            raise RuntimeError("cryptography package is required for AES-256 encryption")
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        nonce = secrets.token_bytes(12)
        assert AESGCM is not None
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, raw, None)
        envelope = nonce + ciphertext
        return base64.b64encode(envelope).decode("utf-8")

    def decrypt_json(self, token: str) -> dict:
        if not self._available:
            raise RuntimeError("cryptography package is required for AES-256 encryption")
        envelope = base64.b64decode(token.encode("utf-8"))
        nonce, ciphertext = envelope[:12], envelope[12:]
        assert AESGCM is not None
        aesgcm = AESGCM(self._key)
        raw = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(raw.decode("utf-8"))


class SignatureService:
    """HMAC-SHA256 signing for financial events and webhook verification."""

    def sign(self, payload: dict, secret: str) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()

    def verify(self, payload: dict, signature: str, secret: str) -> bool:
        expected = self.sign(payload=payload, secret=secret)
        return hmac.compare_digest(expected, signature)


password_hasher = PasswordHasher()
aes256_cipher = Aes256Cipher()
signature_service = SignatureService()
