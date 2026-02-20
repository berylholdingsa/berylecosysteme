"""Service layer for Smart Payment Terminal orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from src.db.sqlalchemy import SessionLocal
from src.observability.logging.logger import logger

from .aoq_adapter import AOQPaymentEngine
from .events import (
    TOPIC_PAYMENT_BLOCKED,
    TOPIC_PAYMENT_CONFIRMED,
    TOPIC_PAYMENT_FLAGGED,
    TOPIC_PAYMENT_INITIATED,
    stage_payment_event,
)
from .schemas import (
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    PaymentDecision,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentSessionResponse,
    PaymentStatus,
)


class PaymentTerminalError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


@dataclass(slots=True)
class PaymentTerminalSession:
    terminal_session_id: str
    transaction_id: str
    amount: str
    currency: str
    merchant_id: str
    payment_method: str
    status: PaymentStatus
    decision: PaymentDecision
    confidence_score: float
    risk_score: float
    ai_flags: list[str]
    metadata: dict[str, Any]
    correlation_id: str
    created_at: str
    updated_at: str


class PaymentTerminalService:
    def __init__(self) -> None:
        self._aoq_engine = AOQPaymentEngine()
        self._sessions: dict[str, PaymentTerminalSession] = {}
        self._lock = RLock()

    def initiate(
        self,
        *,
        request: PaymentInitiateRequest,
        correlation_id: str,
        request_id: str,
    ) -> PaymentInitiateResponse:
        evaluation = self._aoq_engine.evaluate(request)

        terminal_session_id = str(uuid4())
        transaction_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        status = PaymentStatus.BLOCKED if evaluation.decision == PaymentDecision.BLOCK else PaymentStatus.PENDING

        terminal_session = PaymentTerminalSession(
            terminal_session_id=terminal_session_id,
            transaction_id=transaction_id,
            amount=str(request.amount),
            currency=request.currency,
            merchant_id=request.merchant_id,
            payment_method=request.payment_method.value,
            status=status,
            decision=evaluation.decision,
            confidence_score=evaluation.confidence_score,
            risk_score=evaluation.risk_score,
            ai_flags=evaluation.ai_flags,
            metadata=request.metadata,
            correlation_id=correlation_id,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._sessions[terminal_session_id] = terminal_session

        self._stage_initiate_events(
            terminal_session=terminal_session,
            correlation_id=correlation_id,
            request_id=request_id,
        )

        logger.info(
            "event=payment_terminal_initiated",
            transaction_id=transaction_id,
            terminal_session_id=terminal_session_id,
            status=status.value,
            decision=evaluation.decision.value,
            confidence_score=evaluation.confidence_score,
            risk_score=evaluation.risk_score,
            ai_flags=",".join(evaluation.ai_flags),
        )

        return PaymentInitiateResponse(
            status=status,
            decision=evaluation.decision,
            confidence_score=evaluation.confidence_score,
            terminal_session_id=terminal_session_id,
        )

    def confirm(
        self,
        *,
        request: PaymentConfirmRequest,
        correlation_id: str,
        request_id: str,
    ) -> PaymentConfirmResponse:
        if not request.biometric_verified:
            raise PaymentTerminalError(
                status_code=400,
                code="BIOMETRIC_REQUIRED",
                message="biometric verification is required",
            )

        with self._lock:
            terminal_session = self._sessions.get(request.terminal_session_id)

        if terminal_session is None:
            raise PaymentTerminalError(
                status_code=404,
                code="SESSION_NOT_FOUND",
                message="terminal session not found",
                details={"terminal_session_id": request.terminal_session_id},
            )

        if terminal_session.decision == PaymentDecision.BLOCK:
            raise PaymentTerminalError(
                status_code=409,
                code="PAYMENT_BLOCKED",
                message="payment blocked by AOQ decision",
                details={"terminal_session_id": request.terminal_session_id},
            )

        if terminal_session.status == PaymentStatus.CONFIRMED:
            return PaymentConfirmResponse(
                status=terminal_session.status,
                decision=terminal_session.decision,
                confidence_score=terminal_session.confidence_score,
                terminal_session_id=terminal_session.terminal_session_id,
            )

        next_status = PaymentStatus.CONFIRMED
        now = datetime.now(timezone.utc).isoformat()

        self._stage_confirm_events(
            terminal_session=terminal_session,
            next_status=next_status,
            correlation_id=correlation_id,
            request_id=request_id,
        )

        with self._lock:
            terminal_session.status = next_status
            terminal_session.updated_at = now
            if request.metadata:
                terminal_session.metadata = {**terminal_session.metadata, **request.metadata}

        logger.info(
            "event=payment_terminal_confirmed",
            transaction_id=terminal_session.transaction_id,
            terminal_session_id=terminal_session.terminal_session_id,
            status=next_status.value,
            decision=terminal_session.decision.value,
        )

        return PaymentConfirmResponse(
            status=next_status,
            decision=terminal_session.decision,
            confidence_score=terminal_session.confidence_score,
            terminal_session_id=terminal_session.terminal_session_id,
        )

    def get_session(self, *, terminal_session_id: str) -> PaymentSessionResponse:
        with self._lock:
            terminal_session = self._sessions.get(terminal_session_id)

        if terminal_session is None:
            raise PaymentTerminalError(
                status_code=404,
                code="SESSION_NOT_FOUND",
                message="terminal session not found",
                details={"terminal_session_id": terminal_session_id},
            )

        return PaymentSessionResponse(
            status=terminal_session.status,
            risk_score=terminal_session.risk_score,
            ai_flags=terminal_session.ai_flags,
            decision=terminal_session.decision,
            confidence_score=terminal_session.confidence_score,
            transaction_id=terminal_session.transaction_id,
        )

    def _stage_initiate_events(
        self,
        *,
        terminal_session: PaymentTerminalSession,
        correlation_id: str,
        request_id: str,
    ) -> None:
        try:
            with SessionLocal() as session:
                with session.begin():
                    stage_payment_event(
                        session=session,
                        topic=TOPIC_PAYMENT_INITIATED,
                        transaction_id=terminal_session.transaction_id,
                        correlation_id=correlation_id,
                        request_id=request_id,
                        payload={
                            "status": terminal_session.status.value,
                            "decision": terminal_session.decision.value,
                            "confidence_score": terminal_session.confidence_score,
                            "risk_score": terminal_session.risk_score,
                            "ai_flags": terminal_session.ai_flags,
                            "terminal_session_id": terminal_session.terminal_session_id,
                            "amount": terminal_session.amount,
                            "currency": terminal_session.currency,
                            "merchant_id": terminal_session.merchant_id,
                            "payment_method": terminal_session.payment_method,
                        },
                    )
                    if terminal_session.decision == PaymentDecision.BLOCK:
                        stage_payment_event(
                            session=session,
                            topic=TOPIC_PAYMENT_BLOCKED,
                            transaction_id=terminal_session.transaction_id,
                            correlation_id=correlation_id,
                            request_id=request_id,
                            payload={
                                "decision": terminal_session.decision.value,
                                "risk_score": terminal_session.risk_score,
                                "ai_flags": terminal_session.ai_flags,
                                "terminal_session_id": terminal_session.terminal_session_id,
                            },
                        )
                    elif terminal_session.decision == PaymentDecision.REVIEW:
                        stage_payment_event(
                            session=session,
                            topic=TOPIC_PAYMENT_FLAGGED,
                            transaction_id=terminal_session.transaction_id,
                            correlation_id=correlation_id,
                            request_id=request_id,
                            payload={
                                "decision": terminal_session.decision.value,
                                "risk_score": terminal_session.risk_score,
                                "ai_flags": terminal_session.ai_flags,
                                "terminal_session_id": terminal_session.terminal_session_id,
                            },
                        )
        except Exception as exc:
            logger.exception(
                "event=payment_terminal_stage_initiate_failed",
                transaction_id=terminal_session.transaction_id,
                error=str(exc),
            )
            raise PaymentTerminalError(
                status_code=500,
                code="EVENT_STAGE_FAILED",
                message="failed to stage payment events",
                details={"reason": str(exc)},
            ) from exc

    def _stage_confirm_events(
        self,
        *,
        terminal_session: PaymentTerminalSession,
        next_status: PaymentStatus,
        correlation_id: str,
        request_id: str,
    ) -> None:
        try:
            with SessionLocal() as session:
                with session.begin():
                    stage_payment_event(
                        session=session,
                        topic=TOPIC_PAYMENT_CONFIRMED,
                        transaction_id=terminal_session.transaction_id,
                        correlation_id=correlation_id,
                        request_id=request_id,
                        payload={
                            "status": next_status.value,
                            "decision": terminal_session.decision.value,
                            "confidence_score": terminal_session.confidence_score,
                            "risk_score": terminal_session.risk_score,
                            "ai_flags": terminal_session.ai_flags,
                            "terminal_session_id": terminal_session.terminal_session_id,
                        },
                    )
        except Exception as exc:
            logger.exception(
                "event=payment_terminal_stage_confirm_failed",
                transaction_id=terminal_session.transaction_id,
                error=str(exc),
            )
            raise PaymentTerminalError(
                status_code=500,
                code="EVENT_STAGE_FAILED",
                message="failed to stage payment confirmation event",
                details={"reason": str(exc)},
            ) from exc


payment_terminal_service = PaymentTerminalService()
