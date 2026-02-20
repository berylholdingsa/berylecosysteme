"""Unified security middleware for strict bank-grade controls."""

from __future__ import annotations

import json
import uuid
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.errors import unified_error_response
from src.config.settings import settings
from src.core.security.crypto import signature_service
from src.core.security.headers import apply_security_headers
from src.core.security.key_management import key_manager
from src.core.security.rate_limit import redis_rate_limiter
from src.core.security.replay_protection import nonce_replay_protector
from src.core.security.tls import request_uses_tls
from src.observability.logging.correlation import set_correlation_id
from src.observability.metrics.prometheus import metrics


class SecurityMiddleware(BaseHTTPMiddleware):
    """Applies request-level Zero Trust checks before business logic."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        public_paths = {
            "/",
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/token-exchange",
            "/api/v2/esg/health",
            "/api/v2/esg/public-key",
            "/.well-known/greenos-public-key",
        }

        if request.url.path in public_paths:
            response = await call_next(request)
            apply_security_headers(response)
            return response

        correlation_id = request.headers.get("X-Correlation-ID")
        if settings.correlation_id_required and not correlation_id:
            metrics.record_security_incident("missing_correlation_id")
            return unified_error_response(
                request=request,
                status_code=400,
                code="SECURITY_MISSING_CORRELATION_ID",
                message="X-Correlation-ID header required",
            )

        resolved_correlation_id = correlation_id or str(uuid.uuid4())
        request.state.correlation_id = resolved_correlation_id
        set_correlation_id(resolved_correlation_id)

        if settings.enforce_tls and not request_uses_tls(request):
            metrics.record_security_incident("tls_required")
            return unified_error_response(
                request=request,
                status_code=426,
                code="SECURITY_TLS_REQUIRED",
                message="TLS required",
            )

        client_id = request.headers.get("X-Client-Id") or (request.client.host if request.client else "unknown")
        allowed, remaining = redis_rate_limiter.allow(subject=client_id)
        if not allowed:
            metrics.record_security_incident("rate_limit_blocked")
            return unified_error_response(
                request=request,
                status_code=429,
                code="SECURITY_RATE_LIMIT_EXCEEDED",
                message="Rate limit exceeded",
            )

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            nonce = request.headers.get("X-Nonce")
            timestamp = request.headers.get("X-Timestamp")
            if not nonce or not timestamp:
                metrics.record_security_incident("nonce_missing")
                return unified_error_response(
                    request=request,
                    status_code=401,
                    code="SECURITY_NONCE_REQUIRED",
                    message="X-Nonce and X-Timestamp required",
                )

            try:
                ts = int(timestamp)
            except ValueError:
                metrics.record_security_incident("nonce_invalid_timestamp")
                return unified_error_response(
                    request=request,
                    status_code=401,
                    code="SECURITY_NONCE_INVALID_TIMESTAMP",
                    message="Invalid X-Timestamp",
                )

            if not nonce_replay_protector.validate(nonce=nonce, unix_timestamp=ts, subject=client_id):
                metrics.record_signature_failure("replay_or_stale_nonce")
                return unified_error_response(
                    request=request,
                    status_code=401,
                    code="SECURITY_REPLAY_DETECTED",
                    message="Replay attack detected",
                )

        if request.url.path.startswith("/api/v1/fintech/webhooks/psp"):
            signature = request.headers.get("X-PSP-Signature")
            if not signature:
                metrics.record_signature_failure("missing_psp_signature")
                return unified_error_response(
                    request=request,
                    status_code=401,
                    code="SECURITY_MISSING_PSP_SIGNATURE",
                    message="Missing webhook signature",
                )

            body = await request.body()
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = {"raw": body.decode("utf-8", errors="ignore")}

            if not signature_service.verify(payload=payload, signature=signature, secret=key_manager.get_psp_webhook_secret()):
                metrics.record_signature_failure("invalid_psp_signature")
                return unified_error_response(
                    request=request,
                    status_code=401,
                    code="SECURITY_INVALID_PSP_SIGNATURE",
                    message="Invalid webhook signature",
                )

            async def receive_again():
                return {"type": "http.request", "body": body}

            request._receive = receive_again

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = resolved_correlation_id
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        apply_security_headers(response)
        return response
