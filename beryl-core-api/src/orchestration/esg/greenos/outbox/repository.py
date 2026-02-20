"""Repository helpers for GreenOS transactional outbox."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from sqlalchemy import Select, asc, func, select

from src.db.models.esg_greenos import EsgOutboxEventModel
from src.db.sqlalchemy import Base, get_engine, get_session_local


SessionFactory = Callable[[], object]


@dataclass(frozen=True)
class GreenOSOutboxInsert:
    """Insert payload for a GreenOS outbox row."""

    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]


class GreenOSOutboxRepository:
    """Persistence for GreenOS transactional outbox events."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or get_session_local()
        Base.metadata.create_all(bind=get_engine(), tables=[EsgOutboxEventModel.__table__], checkfirst=True)

    @property
    def session_factory(self) -> SessionFactory:
        return self._session_factory

    def enqueue(self, *, session, payload: GreenOSOutboxInsert) -> EsgOutboxEventModel:
        row = EsgOutboxEventModel(
            aggregate_type=payload.aggregate_type,
            aggregate_id=payload.aggregate_id,
            event_type=payload.event_type,
            payload=payload.payload,
            status="PENDING",
            retry_count=0,
            last_attempt_at=None,
        )
        session.add(row)
        session.flush()
        return row

    def claim_pending(self, *, session, limit: int) -> list[EsgOutboxEventModel]:
        stmt: Select[tuple[EsgOutboxEventModel]] = (
            select(EsgOutboxEventModel)
            .where(EsgOutboxEventModel.status == "PENDING")
            .order_by(asc(EsgOutboxEventModel.created_at), asc(EsgOutboxEventModel.id))
            .limit(limit)
        )
        bind = session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def count_pending(*, session) -> int:
        stmt = (
            select(func.count())
            .select_from(EsgOutboxEventModel)
            .where(EsgOutboxEventModel.status == "PENDING")
        )
        return int(session.execute(stmt).scalar_one())

    @staticmethod
    def mark_sent(*, row: EsgOutboxEventModel, attempted_at: datetime | None = None) -> None:
        row.status = "SENT"
        row.last_attempt_at = attempted_at or datetime.now(UTC)

    @staticmethod
    def mark_retry(*, row: EsgOutboxEventModel, attempted_at: datetime | None = None) -> None:
        row.retry_count += 1
        row.status = "PENDING"
        row.last_attempt_at = attempted_at or datetime.now(UTC)

    @staticmethod
    def mark_failed(*, row: EsgOutboxEventModel, attempted_at: datetime | None = None) -> None:
        row.retry_count += 1
        row.status = "FAILED"
        row.last_attempt_at = attempted_at or datetime.now(UTC)
