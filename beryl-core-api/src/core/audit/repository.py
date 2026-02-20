"""Repository for immutable audit chain records."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.audit.audit_event import AuditEvent
from src.db.models.audit_chain import AuditChainEventModel


class AuditRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get_latest_hash(self, session: Session) -> str:
        stmt = (
            select(AuditChainEventModel)
            .order_by(AuditChainEventModel.created_at.desc(), AuditChainEventModel.id.desc())
            .limit(1)
        )
        latest = session.execute(stmt).scalar_one_or_none()
        return latest.current_hash if latest else "GENESIS"

    def append(self, session: Session, event: AuditEvent) -> AuditChainEventModel:
        row = AuditChainEventModel(
            event_id=event.event_id,
            actor_id=event.actor_id,
            action=event.action,
            amount=Decimal(event.amount) if event.amount is not None else None,
            currency=event.currency,
            correlation_id=event.correlation_id,
            previous_hash=event.previous_hash,
            current_hash=event.current_hash,
            signature=event.signature,
            payload=event.payload,
            created_at=event.timestamp,
        )
        session.add(row)
        session.flush()
        return row

    def list_paginated(self, session: Session, *, limit: int, offset: int) -> list[AuditChainEventModel]:
        stmt = (
            select(AuditChainEventModel)
            .order_by(AuditChainEventModel.created_at.desc(), AuditChainEventModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(session.execute(stmt).scalars().all())

    def verify_chain(self, session: Session, verifier) -> tuple[bool, list[str]]:
        stmt = select(AuditChainEventModel).order_by(AuditChainEventModel.created_at.asc(), AuditChainEventModel.id.asc())
        rows = list(session.execute(stmt).scalars().all())
        if not rows:
            return True, []

        issues: list[str] = []
        previous = "GENESIS"
        for row in rows:
            if row.previous_hash != previous:
                issues.append(f"broken_link:{row.event_id}")

            if not verifier(row):
                issues.append(f"invalid_signature_or_hash:{row.event_id}")

            previous = row.current_hash

        return len(issues) == 0, issues
