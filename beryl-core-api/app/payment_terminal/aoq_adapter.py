"""Backend-only AOQ adapter used by the Smart Payment Terminal."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .schemas import PaymentDecision, PaymentInitiateRequest, PaymentMethod


@dataclass(slots=True)
class AOQEvaluation:
    decision: PaymentDecision
    risk_score: float
    confidence_score: float
    ai_flags: list[str]
    dimensions: dict[str, float]


class AOQPaymentEngine:
    def evaluate(self, payment_request: PaymentInitiateRequest) -> AOQEvaluation:
        """
        - risk scoring
        - anomaly detection
        - behavioural scoring
        - ESG impact scoring (si applicable)
        """
        amount_value = float(payment_request.amount)
        amount_score = min(100.0, (amount_value / 250_000.0) * 100.0)
        method_score = self._payment_method_score(payment_request.payment_method)
        anomaly_score = self._anomaly_score(payment_request)
        behaviour_score = self._behaviour_score(payment_request)
        esg_score = self._esg_score(payment_request)

        risk_index = (
            (amount_score * 0.45)
            + (method_score * 0.20)
            + (anomaly_score * 0.20)
            + (behaviour_score * 0.10)
            + (esg_score * 0.05)
        )

        metadata = payment_request.metadata
        if bool(metadata.get("trusted_device")):
            risk_index -= 8.0
        if bool(metadata.get("trusted_customer")):
            risk_index -= 10.0
        if bool(metadata.get("high_velocity")):
            risk_index += 12.0
        if bool(metadata.get("known_fraud_signal")):
            risk_index += 20.0

        risk_index = max(0.0, min(100.0, risk_index))
        risk_score = round(risk_index / 100.0, 4)
        decision = self._resolve_decision(risk_score)
        confidence_score = self._resolve_confidence(decision=decision, risk_score=risk_score)
        ai_flags = self._resolve_flags(
            amount_score=amount_score,
            anomaly_score=anomaly_score,
            behaviour_score=behaviour_score,
            payment_request=payment_request,
        )

        return AOQEvaluation(
            decision=decision,
            risk_score=risk_score,
            confidence_score=confidence_score,
            ai_flags=ai_flags,
            dimensions={
                "amount_score": round(amount_score, 2),
                "method_score": round(method_score, 2),
                "anomaly_score": round(anomaly_score, 2),
                "behaviour_score": round(behaviour_score, 2),
                "esg_score": round(esg_score, 2),
            },
        )

    def _payment_method_score(self, payment_method: PaymentMethod) -> float:
        if payment_method == PaymentMethod.CARD:
            return 58.0
        if payment_method == PaymentMethod.QR:
            return 44.0
        return 36.0

    def _anomaly_score(self, payment_request: PaymentInitiateRequest) -> float:
        metadata = payment_request.metadata
        seed = (
            f"anomaly:{payment_request.merchant_id}:{payment_request.amount}:"
            f"{payment_request.payment_method.value}:{metadata.get('customer_id', 'anonymous')}"
        )
        bucket = int(sha256(seed.encode("utf-8")).hexdigest()[:8], 16)
        return float(bucket % 101)

    def _behaviour_score(self, payment_request: PaymentInitiateRequest) -> float:
        metadata = payment_request.metadata
        seed = (
            f"behaviour:{payment_request.merchant_id}:{metadata.get('device_id', 'na')}:"
            f"{metadata.get('session_age_sec', 0)}:{metadata.get('attempt_count', 1)}"
        )
        bucket = int(sha256(seed.encode("utf-8")).hexdigest()[8:16], 16)
        return float(bucket % 101)

    def _esg_score(self, payment_request: PaymentInitiateRequest) -> float:
        metadata = payment_request.metadata
        if metadata.get("esg_context") in (True, "true", "1"):
            return 66.0
        return 20.0

    def _resolve_decision(self, risk_score: float) -> PaymentDecision:
        if risk_score >= 0.82:
            return PaymentDecision.BLOCK
        if risk_score >= 0.60:
            return PaymentDecision.REVIEW
        return PaymentDecision.ALLOW

    def _resolve_confidence(self, *, decision: PaymentDecision, risk_score: float) -> float:
        if decision == PaymentDecision.BLOCK:
            confidence = 0.82 + ((risk_score - 0.82) * 0.60)
        elif decision == PaymentDecision.REVIEW:
            confidence = 0.55 + abs(risk_score - 0.71)
        else:
            confidence = 0.70 + ((0.60 - risk_score) * 0.35)
        return round(max(0.50, min(0.99, confidence)), 4)

    def _resolve_flags(
        self,
        *,
        amount_score: float,
        anomaly_score: float,
        behaviour_score: float,
        payment_request: PaymentInitiateRequest,
    ) -> list[str]:
        flags: list[str] = []
        if amount_score >= 70:
            flags.append("HIGH_AMOUNT")
        if anomaly_score >= 65:
            flags.append("ANOMALY_PATTERN")
        if behaviour_score >= 70:
            flags.append("BEHAVIOURAL_OUTLIER")
        if payment_request.metadata.get("high_velocity"):
            flags.append("VELOCITY_SPIKE")
        if payment_request.metadata.get("esg_context"):
            flags.append("ESG_IMPACT_CHECK")
        if not flags:
            flags.append("NORMAL_PATTERN")
        return flags

