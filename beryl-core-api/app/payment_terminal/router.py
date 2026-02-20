"""REST API for Smart Payment Terminal."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse

from src.events.outbox_relay import outbox_relay_service
from src.observability.logging.logger import logger

from .schemas import (
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentSessionResponse,
    UnifiedErrorResponse,
)
from .service import PaymentTerminalError, payment_terminal_service


router = APIRouter()


def _resolve_correlation_id(request: Request, header_value: str | None) -> str:
    value = (header_value or request.headers.get("X-Correlation-ID") or str(uuid4())).strip()
    return value or str(uuid4())


def _resolve_request_id(request: Request, correlation_id: str) -> str:
    candidate = request.headers.get("X-Request-ID", "").strip()
    if candidate:
        return candidate
    return correlation_id.split("-")[0]


def _canonical_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def _payload_signature(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload(payload).encode("utf-8")).hexdigest()


def _validate_request_signature(
    *,
    payload: dict[str, Any],
    provided_signature: str | None,
) -> bool:
    if not provided_signature:
        return False
    normalized = provided_signature.strip().lower()
    if not normalized:
        return False
    expected_signature = _payload_signature(payload)
    return hmac.compare_digest(normalized, expected_signature)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    correlation_id: str,
    request_id: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = UnifiedErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers={"X-Correlation-ID": correlation_id},
    )


@router.post("/payments/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request_payload: PaymentInitiateRequest,
    http_request: Request,
    http_response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    x_request_signature: str | None = Header(default=None, alias="X-Request-Signature"),
):
    correlation_id = _resolve_correlation_id(http_request, x_correlation_id)
    request_id = _resolve_request_id(http_request, correlation_id)
    http_response.headers["X-Correlation-ID"] = correlation_id

    if not _validate_request_signature(
        payload=request_payload.model_dump(mode="json"),
        provided_signature=x_request_signature,
    ):
        return _error_response(
            status_code=401,
            code="INVALID_REQUEST_SIGNATURE",
            message="request signature validation failed",
            details={"header": "X-Request-Signature"},
            correlation_id=correlation_id,
            request_id=request_id,
        )

    try:
        result = payment_terminal_service.initiate(
            request=request_payload,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        await outbox_relay_service.publish_pending(limit=200)
        return result
    except PaymentTerminalError as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            correlation_id=correlation_id,
            request_id=request_id,
        )
    except Exception as exc:
        logger.exception(
            "event=payment_terminal_initiate_failed",
            error=str(exc),
            correlation_id=correlation_id,
            request_id=request_id,
        )
        return _error_response(
            status_code=500,
            code="PAYMENT_TERMINAL_ERROR",
            message="unexpected payment terminal failure",
            details={"reason": str(exc)},
            correlation_id=correlation_id,
            request_id=request_id,
        )


@router.post("/payments/confirm", response_model=PaymentConfirmResponse)
async def confirm_payment(
    request_payload: PaymentConfirmRequest,
    http_request: Request,
    http_response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    x_request_signature: str | None = Header(default=None, alias="X-Request-Signature"),
):
    correlation_id = _resolve_correlation_id(http_request, x_correlation_id)
    request_id = _resolve_request_id(http_request, correlation_id)
    http_response.headers["X-Correlation-ID"] = correlation_id

    if not _validate_request_signature(
        payload=request_payload.model_dump(mode="json"),
        provided_signature=x_request_signature,
    ):
        return _error_response(
            status_code=401,
            code="INVALID_REQUEST_SIGNATURE",
            message="request signature validation failed",
            details={"header": "X-Request-Signature"},
            correlation_id=correlation_id,
            request_id=request_id,
        )

    try:
        result = payment_terminal_service.confirm(
            request=request_payload,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        await outbox_relay_service.publish_pending(limit=200)
        return result
    except PaymentTerminalError as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            correlation_id=correlation_id,
            request_id=request_id,
        )
    except Exception as exc:
        logger.exception(
            "event=payment_terminal_confirm_failed",
            error=str(exc),
            correlation_id=correlation_id,
            request_id=request_id,
        )
        return _error_response(
            status_code=500,
            code="PAYMENT_TERMINAL_ERROR",
            message="unexpected payment terminal failure",
            details={"reason": str(exc)},
            correlation_id=correlation_id,
            request_id=request_id,
        )


@router.get("/payments/session/{terminal_session_id}", response_model=PaymentSessionResponse)
def get_payment_session(
    terminal_session_id: str,
    http_request: Request,
    http_response: Response,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
):
    correlation_id = _resolve_correlation_id(http_request, x_correlation_id)
    request_id = _resolve_request_id(http_request, correlation_id)
    http_response.headers["X-Correlation-ID"] = correlation_id

    try:
        return payment_terminal_service.get_session(terminal_session_id=terminal_session_id)
    except PaymentTerminalError as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            correlation_id=correlation_id,
            request_id=request_id,
        )
    except Exception as exc:
        logger.exception(
            "event=payment_terminal_session_fetch_failed",
            error=str(exc),
            correlation_id=correlation_id,
            request_id=request_id,
        )
        return _error_response(
            status_code=500,
            code="PAYMENT_TERMINAL_ERROR",
            message="unexpected payment terminal failure",
            details={"reason": str(exc)},
            correlation_id=correlation_id,
            request_id=request_id,
        )
