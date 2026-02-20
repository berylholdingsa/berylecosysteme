"""Immutable audit chain service for regulated transaction traceability."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from sqlalchemy.orm import Session

from src.config.settings import settings
from src.core.audit.audit_event import AuditEvent
from src.core.audit.immutable_writer import ImmutableAuditWriter
from src.core.audit.repository import AuditRepository
from src.db.models.audit_chain import AuditChainEventModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class AuditService:
    def __init__(self, session_factory: Callable[[], Session] = lambda: get_session_local()()):
        self._repository = AuditRepository(session_factory=session_factory)
        self._writer = ImmutableAuditWriter(repository=self._repository)
        self._session_factory = session_factory
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[AuditChainEventModel.__table__],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=audit_chain_bootstrap_skipped reason={str(exc)}")

    def record_financial_event(
        self,
        *,
        session: Session,
        actor_id: str,
        action: str,
        amount: Decimal | None,
        currency: str | None,
        correlation_id: str,
        payload: dict,
    ) -> AuditChainEventModel:
        started = time.perf_counter()
        previous_hash = session.info.get("audit_last_hash")
        if previous_hash is None:
            previous_hash = self._repository.get_latest_hash(session)
        current_hash = self._compute_current_hash(
            actor_id=actor_id,
            action=action,
            amount=amount,
            currency=currency,
            correlation_id=correlation_id,
            previous_hash=previous_hash,
            payload=payload,
        )
        signature = self._sign_current_hash(current_hash)

        event = AuditEvent.build(
            actor_id=actor_id,
            action=action,
            amount=amount,
            currency=currency,
            correlation_id=correlation_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            signature=signature,
            payload=payload,
        )

        written = self._writer.write(session=session, event=event)
        session.info["audit_last_hash"] = written.current_hash
        latency_ms = (time.perf_counter() - started) * 1000
        metrics.record_audit_write_latency(latency_ms)
        return written

    def list_events(self, *, limit: int = 50, offset: int = 0) -> list[AuditChainEventModel]:
        with self._session_factory() as session:
            return self._repository.list_paginated(session, limit=limit, offset=offset)

    def verify_integrity(self) -> tuple[bool, list[str]]:
        with self._session_factory() as session:
            ok, issues = self._repository.verify_chain(session=session, verifier=self._verify_row)
            if not ok:
                metrics.record_audit_integrity_failure(len(issues))
            return ok, issues

    def _compute_current_hash(
        self,
        *,
        actor_id: str,
        action: str,
        amount: Decimal | None,
        currency: str | None,
        correlation_id: str,
        previous_hash: str,
        payload: dict,
    ) -> str:
        material = {
            "actor_id": actor_id,
            "action": action,
            "amount": self._normalize_amount(amount),
            "currency": currency,
            "correlation_id": correlation_id,
            "previous_hash": previous_hash,
            "payload": payload,
        }
        canonical = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_amount(amount: Decimal | None) -> str | None:
        if amount is None:
            return None
        return str(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def _sign_current_hash(self, current_hash: str) -> str:
        return hmac.new(
            settings.audit_secret_key.encode("utf-8"),
            current_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _verify_row(self, row: AuditChainEventModel) -> bool:
        expected_hash = self._compute_current_hash(
            actor_id=row.actor_id,
            action=row.action,
            amount=row.amount,
            currency=row.currency,
            correlation_id=row.correlation_id,
            previous_hash=row.previous_hash,
            payload=row.payload,
        )
        if expected_hash != row.current_hash:
            return False

        expected_signature = self._sign_current_hash(row.current_hash)
        return hmac.compare_digest(expected_signature, row.signature)


audit_service = AuditService()
