"""Backend-only transaction risk scoring for AML and suspicious activity handling."""

from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import settings
from src.compliance.anomaly_detector import anomaly_detector
from src.compliance.sanction_list_checker import sanction_list_checker
from src.compliance.velocity_checker import velocity_checker


@dataclass(frozen=True)
class RiskAssessment:
    score: float
    reasons: list[str]
    flagged: bool


class TransactionRiskScorer:
    def __init__(self) -> None:
        self.threshold = settings.compliance_risk_threshold
        self.amount_threshold = settings.compliance_transaction_amount_threshold

    def assess(self, *, actor_id: str, amount: float, currency: str) -> RiskAssessment:
        score = 0.0
        reasons: list[str] = []

        if velocity_checker.is_velocity_exceeded(actor_id):
            score += 35.0
            reasons.append("velocity_limit_exceeded")

        if amount >= self.amount_threshold:
            score += 25.0
            reasons.append("high_amount_threshold")

        if sanction_list_checker.is_sanctioned(actor_id):
            score += 60.0
            reasons.append("sanctions_match")

        if anomaly_detector.evaluate(actor_id=actor_id, amount=amount):
            score += 20.0
            reasons.append("behavior_anomaly")

        normalized = min(100.0, score)
        flagged = normalized >= self.threshold
        return RiskAssessment(score=normalized, reasons=reasons, flagged=flagged)


transaction_risk_scorer = TransactionRiskScorer()
