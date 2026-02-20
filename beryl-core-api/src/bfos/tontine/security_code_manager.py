"""Security code hashing and verification for Tontine sensitive actions."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import re

from src.config.settings import settings
from src.observability.logging.logger import logger


_CODE_PATTERN = re.compile(r"^\d{5}$")
_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000


class SecurityCodeManager:
    """Manage secure hashing of 5-digit Tontine shared code."""

    def __init__(self, *, pepper: str | None = None) -> None:
        self._pepper = (pepper or settings.bfos_tontine_security_code_pepper).encode("utf-8")

    @staticmethod
    def _validate_code_format(code: str) -> str:
        candidate = code.strip()
        if not _CODE_PATTERN.match(candidate):
            raise ValueError("security_code must be exactly 5 numeric digits")
        return candidate

    def hash_security_code(self, code: str) -> str:
        normalized = self._validate_code_format(code)
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            normalized.encode("utf-8"),
            f"{salt}:{self._pepper.decode('utf-8')}".encode("utf-8"),
            _ITERATIONS,
        ).hex()
        value = f"{_ALGORITHM}${_ITERATIONS}${salt}${digest}"
        logger.info("event=tontine_security_code_hashed")
        return value

    def verify_security_code(self, code: str, stored_hash: str) -> bool:
        try:
            normalized = self._validate_code_format(code)
            algorithm, iterations, salt, expected_digest = stored_hash.split("$", 3)
            if algorithm != _ALGORITHM:
                return False
            recomputed = hashlib.pbkdf2_hmac(
                "sha256",
                normalized.encode("utf-8"),
                f"{salt}:{self._pepper.decode('utf-8')}".encode("utf-8"),
                int(iterations),
            ).hex()
            return hmac.compare_digest(expected_digest, recomputed)
        except Exception:  # pragma: no cover - defensive parser
            return False


security_code_manager = SecurityCodeManager()


def hash_security_code(code: str) -> str:
    return security_code_manager.hash_security_code(code)


def verify_security_code(code: str, stored_hash: str) -> bool:
    return security_code_manager.verify_security_code(code, stored_hash)
