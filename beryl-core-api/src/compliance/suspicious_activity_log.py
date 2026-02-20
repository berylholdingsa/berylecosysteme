"""Suspicious activity log persistence and event flagging."""

from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy.orm import Session

from src.db.models.compliance import SuspiciousActivityLogModel


class SuspiciousActivityLogService:
    def record(
        self,
        *,
        session: Session,
        transaction_id: str,
        actor_id: str,
        risk_score: float,
        reasons: list[str],
        correlation_id: str,
    ) -> SuspiciousActivityLogModel:
        row = SuspiciousActivityLogModel(
            transaction_id=transaction_id,
            actor_id=actor_id,
            risk_score=Decimal(str(round(risk_score, 2))),
            reasons=json.dumps(reasons, sort_keys=True),
            correlation_id=correlation_id,
        )
        session.add(row)
        session.flush()
        return row


suspicious_activity_log_service = SuspiciousActivityLogService()
