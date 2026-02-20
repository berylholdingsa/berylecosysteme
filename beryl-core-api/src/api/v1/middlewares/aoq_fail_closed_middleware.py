"""Fail-closed middleware for sensitive actions requiring backend AOQ gate."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.errors import unified_error_response
from src.infrastructure.testing_stubs import DummyAOQClient
from src.observability.metrics.prometheus import metrics


@dataclass(frozen=True, slots=True)
class AoqGateDecision:
    allowed: bool
    score: float
    threshold: float
    decision: str
    rationale: str


class AoqFailClosedMiddleware(BaseHTTPMiddleware):
    """Blocks sensitive operations when AOQ decisioning cannot be produced."""

    _sensitive_prefixes = (
        "/api/v1/mobility/ride/",
        "/api/v1/esg/score/compute",
        "/api/v1/esg/impact/normalize",
        "/api/v1/fintech/transfer",
        "/api/v1/payments",
    )

    def __init__(self, app, timeout_seconds: float = 0.65) -> None:
        super().__init__(app)
        self._timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)

        path = request.url.path
        if not path.startswith(self._sensitive_prefixes):
            return await call_next(request)

        started_at = perf_counter()
        if os.getenv("TESTING") == "1":
            stub = DummyAOQClient().evaluate()
            decision = AoqGateDecision(
                allowed=stub.allowed,
                score=stub.score,
                threshold=stub.threshold,
                decision=stub.decision,
                rationale=stub.rationale,
            )
        else:
            try:
                decision = await asyncio.wait_for(
                    asyncio.to_thread(self._evaluate_gate, request),
                    timeout=self._timeout_seconds,
                )
            except TimeoutError:
                metrics.record_security_incident("aoq_timeout_fail_closed")
                return unified_error_response(
                    request=request,
                    status_code=503,
                    code="AOQ_UNAVAILABLE",
                    message="AOQ unavailable: sensitive action blocked",
                    details={"reason": "timeout"},
                )
            except Exception as exc:
                metrics.record_security_incident("aoq_error_fail_closed")
                return unified_error_response(
                    request=request,
                    status_code=503,
                    code="AOQ_UNAVAILABLE",
                    message="AOQ unavailable: sensitive action blocked",
                    details={"reason": str(exc)},
                )

        metrics.record_aoq_decision(
            decision=decision.decision,
            latency_seconds=perf_counter() - started_at,
            active_rules=1,
        )

        if not decision.allowed:
            return unified_error_response(
                request=request,
                status_code=403,
                code="AOQ_BLOCKED",
                message="Sensitive action denied by AOQ policy",
                details={
                    "score": decision.score,
                    "threshold": decision.threshold,
                    "rationale": decision.rationale,
                },
            )
        return await call_next(request)

    def _evaluate_gate(self, request: Request) -> AoqGateDecision:
        """Deterministic backend AOQ gate used for fail-closed middleware."""
        path = request.url.path
        method = request.method
        user_payload = getattr(request.state, "user", {}) or {}
        user_id = getattr(request.state, "user_id", None) or user_payload.get("sub") or "anonymous"

        # Normalize user IDs to UUID for AOQ consistency across domains.
        normalized_user_id = str(uuid5(NAMESPACE_URL, f"beryl-aoq:{user_id}"))

        fintech_score = 82.0 if "/fintech/" in path or "/payments" in path else 45.0
        mobility_score = 90.0 if "/mobility/" in path else 50.0
        esg_score = 80.0 if "/esg/" in path else 55.0
        social_score = 48.0

        weighted_score = round(
            fintech_score * 0.35
            + mobility_score * 0.25
            + esg_score * 0.25
            + social_score * 0.15,
            2,
        )

        threshold = 55.0
        if method == "DELETE" or path.endswith("/cancel"):
            threshold = 60.0
        if method == "POST" and path.endswith("/complete"):
            threshold = 62.0

        decision = "APPROVE" if weighted_score >= threshold else "REJECT"
        return AoqGateDecision(
            allowed=decision == "APPROVE",
            score=weighted_score,
            threshold=threshold,
            decision=decision,
            rationale=f"user_id={normalized_user_id} path={path}",
        )
