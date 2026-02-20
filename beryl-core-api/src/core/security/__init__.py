"""Security primitives for bank-grade controls."""

from src.core.security.crypto import aes256_cipher, password_hasher, signature_service
from src.core.security.jwt_rotation import jwt_rotation_service
from src.core.security.key_management import key_manager
from src.core.security.middleware import SecurityMiddleware
from src.core.security.rate_limit import redis_rate_limiter
from src.core.security.replay_protection import nonce_replay_protector

try:
    from src.core.security.idempotency import idempotency_service
except Exception:  # pragma: no cover - optional dependency in constrained envs
    idempotency_service = None

__all__ = [
    "SecurityMiddleware",
    "aes256_cipher",
    "password_hasher",
    "signature_service",
    "idempotency_service",
    "jwt_rotation_service",
    "key_manager",
    "redis_rate_limiter",
    "nonce_replay_protector",
]
