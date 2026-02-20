"""Unified API error helpers for v1 endpoints and middleware."""

from __future__ import annotations

from typing import Any
import uuid

from fastapi import Request
from starlette.responses import JSONResponse


def resolve_correlation_id(request: Request) -> str:
    """Resolve correlation ID from request context or generate one."""
    header_value = request.headers.get("X-Correlation-ID")
    if header_value:
        return header_value

    state_value = getattr(request.state, "correlation_id", None)
    if state_value:
        return str(state_value)

    trace_value = getattr(request.state, "trace_id", None)
    if trace_value:
        return str(trace_value)

    return str(uuid.uuid4())


def unified_error_payload(
    *,
    request: Request,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical API error payload."""
    return {
        "code": code,
        "message": message,
        "details": details or {},
        "correlation_id": resolve_correlation_id(request),
    }


def unified_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Create canonical error response object."""
    return JSONResponse(
        status_code=status_code,
        content=unified_error_payload(
            request=request,
            code=code,
            message=message,
            details=details,
        ),
    )
