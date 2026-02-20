"""
Error handler middleware for the Beryl Core API.

This module provides middleware for handling errors.
"""

from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.errors import unified_error_response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for error handling."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            detail: Any = exc.detail
            if isinstance(detail, dict):
                return unified_error_response(
                    request=request,
                    status_code=exc.status_code,
                    code=str(detail.get("code", "HTTP_ERROR")),
                    message=str(detail.get("message", "Request failed")),
                    details=detail.get("details") if isinstance(detail.get("details"), dict) else {},
                )

            return unified_error_response(
                request=request,
                status_code=exc.status_code,
                code=f"HTTP_{exc.status_code}",
                message=str(detail),
                details={},
            )
        except Exception:
            return unified_error_response(
                request=request,
                status_code=500,
                code="INTERNAL_SERVER_ERROR",
                message="Internal server error",
                details={},
            )
