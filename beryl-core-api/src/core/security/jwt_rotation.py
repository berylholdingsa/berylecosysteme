"""JWT issuance and verification with key rotation support."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.config.settings import settings
from src.core.security.key_management import KeyManager, SigningKey, key_manager


class TokenValidationError(RuntimeError):
    """Raised when token verification fails."""


@dataclass(frozen=True)
class RotatingToken:
    token: str
    kid: str
    expires_at: datetime


class JwtRotationService:
    """Maintains active and grace keys for token validation."""

    def __init__(self, manager: KeyManager | None = None) -> None:
        self._manager = manager or key_manager
        self._signing_keys = self._manager.get_signing_keys()
        self._active_kid = settings.jwt_active_kid
        self._grace_keys: dict[str, datetime] = {}

    def issue_access_token(self, payload: dict, expires_delta: timedelta | None = None) -> RotatingToken:
        now = datetime.now(timezone.utc)
        ttl = expires_delta or timedelta(minutes=settings.jwt_expiration_minutes)
        expires_at = now + ttl

        claims = payload.copy()
        claims.update(
            {
                "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            }
        )

        signing_key = self._active_signing_key()
        token = jwt.encode(
            claims,
            signing_key.secret,
            algorithm=settings.jwt_algorithm,
            headers={"kid": signing_key.kid},
        )
        return RotatingToken(token=token, kid=signing_key.kid, expires_at=expires_at)

    def verify(self, token: str) -> dict:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        candidate_keys = []

        if kid and kid in self._signing_keys:
            candidate_keys.append(self._signing_keys[kid].secret)
        else:
            candidate_keys.extend(key.secret for key in self._signing_keys.values())

        for secret in candidate_keys:
            try:
                return jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
            except JWTError:
                continue

        raise TokenValidationError("Invalid or expired token")

    def rotate_now(self, new_secret: str | None = None, new_kid: str | None = None) -> str:
        current_key = self._active_signing_key()
        grace_deadline = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_rotation_grace_minutes)
        self._grace_keys[current_key.kid] = grace_deadline

        kid = new_kid or datetime.now(timezone.utc).strftime("kid-%Y%m%d%H%M%S")
        secret = new_secret or self._manager.generate_key_material(48)
        self._signing_keys[kid] = SigningKey(
            kid=kid,
            secret=secret,
            created_at=datetime.now(timezone.utc),
        )
        self._active_kid = kid
        self._purge_expired_grace_keys()
        return kid

    def _active_signing_key(self) -> SigningKey:
        if self._active_kid in self._signing_keys:
            return self._signing_keys[self._active_kid]
        return self._manager.get_active_signing_key()

    def _purge_expired_grace_keys(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [kid for kid, deadline in self._grace_keys.items() if deadline < now]
        for kid in expired:
            self._grace_keys.pop(kid, None)


jwt_rotation_service = JwtRotationService()
