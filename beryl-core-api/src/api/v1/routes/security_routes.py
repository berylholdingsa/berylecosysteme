"""Security primitives routes (signature challenge/verify)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import hmac
import time
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.core.security.key_management import key_manager

router = APIRouter()

_CHALLENGE_TTL_SECONDS = max(90, settings.nonce_ttl_seconds)
_ROTATION_WINDOW_SECONDS = max(60, settings.nonce_ttl_seconds)
_IDEMPOTENCY_TTL_SECONDS = 3600


@dataclass(slots=True)
class SignatureChallengeRecord:
    challenge_id: str
    user_id: str
    scope: str
    payload_hash: str
    nonce: str
    timestamp: int
    expires_at: int
    used: bool = False


class SignatureChallengeRequest(BaseModel):
    scope: str = Field(min_length=3, max_length=64)
    payload_hash: str = Field(min_length=16, max_length=128)


class SignatureChallengeResponse(BaseModel):
    challenge_id: str
    nonce: str
    timestamp: int
    expires_at: str
    algorithm: str = "HMAC-SHA256"


class SignatureVerifyRequest(BaseModel):
    challenge_id: str = Field(min_length=8, max_length=64)
    payload_hash: str = Field(min_length=16, max_length=128)
    signature: str = Field(min_length=32, max_length=256)


class SignatureVerifyResponse(BaseModel):
    verified: bool
    challenge_id: str
    verification_id: str
    verified_at: str


_challenges: dict[str, SignatureChallengeRecord] = {}
_idempotency: dict[str, int] = {}


def _now_ts() -> int:
    return int(time.time())


def _cleanup_stores(now_ts: int) -> None:
    stale_idempotency = [k for k, expires_at in _idempotency.items() if expires_at <= now_ts]
    for key in stale_idempotency:
        _idempotency.pop(key, None)

    stale_challenges = [k for k, challenge in _challenges.items() if challenge.expires_at <= now_ts]
    for key in stale_challenges:
        _challenges.pop(key, None)


def _claim_idempotency(request: Request, idempotency_key: str, operation: str) -> None:
    user_id = getattr(request.state, "user_id", "anonymous")
    key = f"{operation}:{user_id}:{idempotency_key}"
    now_ts = _now_ts()
    _cleanup_stores(now_ts)
    if key in _idempotency:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SECURITY_IDEMPOTENCY_CONFLICT",
                "message": "Duplicate Idempotency-Key",
                "details": {"operation": operation},
            },
        )
    _idempotency[key] = now_ts + _IDEMPOTENCY_TTL_SECONDS


def _rotation_secret(*, unix_ts: int, delta_window: int = 0) -> str:
    window = (unix_ts // _ROTATION_WINDOW_SECONDS) + delta_window
    base_secret = key_manager.get_event_hmac_secret()
    return hmac.new(
        base_secret.encode("utf-8"),
        f"signature-window:{window}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _challenge_payload(record: SignatureChallengeRecord) -> str:
    return (
        f"{record.challenge_id}:{record.nonce}:{record.timestamp}:"
        f"{record.payload_hash}:{record.scope}"
    )


@router.post(
    "/signature/challenge",
    status_code=status.HTTP_201_CREATED,
    response_model=SignatureChallengeResponse,
)
def create_signature_challenge(
    request: Request,
    payload: SignatureChallengeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SECURITY_IDEMPOTENCY_REQUIRED",
                "message": "Idempotency-Key header required",
                "details": {},
            },
        )

    _claim_idempotency(request, idempotency_key, "signature_challenge")

    now_ts = _now_ts()
    challenge_id = str(uuid4())
    challenge = SignatureChallengeRecord(
        challenge_id=challenge_id,
        user_id=str(getattr(request.state, "user_id", "anonymous")),
        scope=payload.scope,
        payload_hash=payload.payload_hash,
        nonce=uuid4().hex,
        timestamp=now_ts,
        expires_at=now_ts + _CHALLENGE_TTL_SECONDS,
    )
    _challenges[challenge_id] = challenge

    return SignatureChallengeResponse(
        challenge_id=challenge.challenge_id,
        nonce=challenge.nonce,
        timestamp=challenge.timestamp,
        expires_at=datetime.fromtimestamp(challenge.expires_at, tz=UTC).isoformat(),
    )


@router.post("/signature/verify", response_model=SignatureVerifyResponse)
def verify_signature(
    request: Request,
    payload: SignatureVerifyRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SECURITY_IDEMPOTENCY_REQUIRED",
                "message": "Idempotency-Key header required",
                "details": {},
            },
        )

    _claim_idempotency(request, idempotency_key, "signature_verify")

    now_ts = _now_ts()
    _cleanup_stores(now_ts)
    challenge = _challenges.get(payload.challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SECURITY_CHALLENGE_NOT_FOUND",
                "message": "Signature challenge not found",
                "details": {"challenge_id": payload.challenge_id},
            },
        )

    if challenge.used:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SECURITY_REPLAY_DETECTED",
                "message": "Challenge already used",
                "details": {"challenge_id": challenge.challenge_id},
            },
        )

    if challenge.expires_at <= now_ts:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "SECURITY_CHALLENGE_EXPIRED",
                "message": "Challenge expired",
                "details": {"challenge_id": challenge.challenge_id},
            },
        )

    if payload.payload_hash != challenge.payload_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SECURITY_PAYLOAD_HASH_MISMATCH",
                "message": "Payload hash mismatch",
                "details": {"challenge_id": challenge.challenge_id},
            },
        )

    canonical_payload = _challenge_payload(challenge)
    candidate_signatures = [
        hmac.new(
            _rotation_secret(unix_ts=challenge.timestamp, delta_window=window_offset).encode("utf-8"),
            canonical_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        for window_offset in (0, -1, 1)
    ]
    is_valid = any(hmac.compare_digest(payload.signature, expected) for expected in candidate_signatures)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "SECURITY_SIGNATURE_INVALID",
                "message": "Invalid signature",
                "details": {"challenge_id": challenge.challenge_id},
            },
        )

    challenge.used = True
    verification_id = str(uuid4())
    return SignatureVerifyResponse(
        verified=True,
        challenge_id=challenge.challenge_id,
        verification_id=verification_id,
        verified_at=datetime.now(tz=UTC).isoformat(),
    )
