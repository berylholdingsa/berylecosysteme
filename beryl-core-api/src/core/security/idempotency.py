"""Database-backed idempotency guard for fintech operations."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from src.db.models.idempotency import IdempotencyKeyModel
from src.db.sqlalchemy import Base, get_engine
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class IdempotencyService:
    def __init__(self) -> None:
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[IdempotencyKeyModel.__table__],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=idempotency_bootstrap_skipped reason={str(exc)}")

    def claim_or_reject(self, *, session, key: str, user_id: str) -> bool:
        try:
            with session.begin_nested():
                row = IdempotencyKeyModel(key=key, user_id=user_id)
                session.add(row)
                session.flush()
            return True
        except IntegrityError:
            metrics.record_idempotency_rejection(scope="transaction")
            return False


idempotency_service = IdempotencyService()
