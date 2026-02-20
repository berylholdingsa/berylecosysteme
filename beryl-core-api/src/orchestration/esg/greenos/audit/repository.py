"""Repository for GreenOS audit metadata records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import Select, and_, desc, or_, select

from src.db.models.esg_greenos import EsgAuditMetadataModel
from src.db.sqlalchemy import Base, get_engine, get_session_local


SessionFactory = Callable[[], object]


@dataclass(frozen=True)
class AuditMetadataInsert:
    """Insert payload for persisted audit metadata."""

    window_label: str
    window_start: datetime
    window_end: datetime
    country_code: str | None
    methodology_id: str
    model_version: str
    report_hash: str
    signature: str
    signature_algorithm: str
    key_version: str
    trips_count: int
    total_distance_km: Decimal
    total_co2_avoided_kg: Decimal
    correlation_id: str
    payload: dict[str, Any]


class AuditMetadataRepository:
    """Append-only storage for GreenOS audit metadata."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or get_session_local()
        Base.metadata.create_all(bind=get_engine(), tables=[EsgAuditMetadataModel.__table__], checkfirst=True)

    @property
    def session_factory(self) -> SessionFactory:
        return self._session_factory

    def create(self, payload: AuditMetadataInsert) -> EsgAuditMetadataModel:
        with self._session_factory() as session:
            record = self.create_in_session(session=session, payload=payload)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def create_in_session(self, *, session, payload: AuditMetadataInsert) -> EsgAuditMetadataModel:
        record = EsgAuditMetadataModel(
            window_label=payload.window_label,
            window_start=payload.window_start,
            window_end=payload.window_end,
            country_code=payload.country_code,
            methodology_id=payload.methodology_id,
            model_version=payload.model_version,
            report_hash=payload.report_hash,
            signature=payload.signature,
            signature_algorithm=payload.signature_algorithm,
            key_version=payload.key_version,
            trips_count=payload.trips_count,
            total_distance_km=payload.total_distance_km,
            total_co2_avoided_kg=payload.total_co2_avoided_kg,
            correlation_id=payload.correlation_id,
            payload=payload.payload,
        )
        session.add(record)
        session.flush()
        return record

    def list_related_to_trip(
        self,
        *,
        event_timestamp: datetime,
        country_code: str,
        limit: int = 50,
    ) -> list[EsgAuditMetadataModel]:
        with self._session_factory() as session:
            stmt: Select[tuple[EsgAuditMetadataModel]] = (
                select(EsgAuditMetadataModel)
                .where(
                    and_(
                        EsgAuditMetadataModel.window_start <= event_timestamp,
                        EsgAuditMetadataModel.window_end >= event_timestamp,
                        or_(
                            EsgAuditMetadataModel.country_code.is_(None),
                            EsgAuditMetadataModel.country_code == country_code,
                        ),
                    )
                )
                .order_by(desc(EsgAuditMetadataModel.created_at))
                .limit(limit)
            )
            return list(session.execute(stmt).scalars().all())
