"""Authentication routes with rotating JWT keys and bcrypt hashing."""

from __future__ import annotations

from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.api.v1.schemas.fintech_schema import AuthRequest, AuthResponse
from src.auth.firebase_verify import verify_id_token
from src.core.security.crypto import password_hasher
from src.core.security.jwt_rotation import jwt_rotation_service

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=8, max_length=256)


class TokenExchangeRequest(BaseModel):
    firebase_id_token: str = Field(min_length=16, max_length=8192)
    requested_scopes: list[str] = Field(default_factory=list)


class TokenExchangeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    scopes: list[str]


class _InMemoryAuthStore:
    """Minimal auth store for API contract and security middleware validation."""

    def __init__(self) -> None:
        self._users: dict[str, str] = {}

    def register(self, username: str, password: str) -> None:
        if username in self._users:
            raise ValueError("user already exists")
        self._users[username] = password_hasher.hash_password(password)

    def verify(self, username: str, password: str) -> bool:
        hashed = self._users.get(username)
        if not hashed:
            return False
        return password_hasher.verify_password(password, hashed)


auth_store = _InMemoryAuthStore()


def _issue_token(username: str) -> str:
    rotating = jwt_rotation_service.issue_access_token(
        payload={
            "sub": username,
            "scopes": ["fintech", "mobility", "esg", "social", "aoq"],
            "domain": "user",
        },
        expires_delta=timedelta(minutes=60),
    )
    return rotating.token


@router.post("/login", response_model=AuthResponse)
def login(request: AuthRequest):
    if not auth_store.verify(request.username, request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = _issue_token(request.username)
    return AuthResponse(access_token=token, token_type="bearer")


@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest):
    try:
        auth_store.register(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    token = _issue_token(request.username)
    return AuthResponse(access_token=token, token_type="bearer")


@router.post("/rotate-keys")
def rotate_keys(http_request: Request):
    user = getattr(http_request.state, "user", {})
    scopes = set(user.get("scopes", []))
    if "admin" not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin scope required")
    kid = jwt_rotation_service.rotate_now()
    return {"status": "ok", "active_kid": kid}


@router.post("/logout")
def logout():
    return {"status": "ok"}


@router.post("/token-exchange", response_model=TokenExchangeResponse)
def token_exchange(request: TokenExchangeRequest):
    try:
        firebase_claims = verify_id_token(request.firebase_id_token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_TOKEN_EXCHANGE_FAILED",
                "message": "Invalid Firebase token",
                "details": {"reason": str(exc)},
            },
        ) from exc

    firebase_uid = str(
        firebase_claims.get("uid")
        or firebase_claims.get("sub")
        or firebase_claims.get("user_id")
        or ""
    ).strip()
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_TOKEN_EXCHANGE_FAILED",
                "message": "Firebase token missing subject",
                "details": {},
            },
        )

    allowed_scopes = ["fintech", "mobility", "esg", "social", "aoq"]
    requested = set(request.requested_scopes) if request.requested_scopes else set(allowed_scopes)
    scopes = [scope for scope in allowed_scopes if scope in requested]
    if not scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AUTH_SCOPE_INVALID",
                "message": "At least one valid scope is required",
                "details": {"allowed_scopes": allowed_scopes},
            },
        )

    internal_subject = str(uuid5(NAMESPACE_URL, f"beryl-firebase:{firebase_uid}"))
    expires_delta = timedelta(minutes=60)
    rotating = jwt_rotation_service.issue_access_token(
        payload={
            "sub": internal_subject,
            "firebase_uid": firebase_uid,
            "scopes": scopes,
            "domain": "user",
        },
        expires_delta=expires_delta,
    )
    return TokenExchangeResponse(
        access_token=rotating.token,
        token_type="bearer",
        expires_in_seconds=int(expires_delta.total_seconds()),
        scopes=scopes,
    )
