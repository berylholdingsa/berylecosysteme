"""Compatibility middleware wrapping Redis-backed limiter."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.security.rate_limit import redis_rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Legacy middleware kept for compatibility with prior imports."""

    async def dispatch(self, request: Request, call_next):
        subject = request.headers.get("X-Client-Id") or (request.client.host if request.client else "unknown")
        allowed, remaining = redis_rate_limiter.allow(subject)
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
