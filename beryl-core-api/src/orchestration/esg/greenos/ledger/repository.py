"""Repository for append-only GreenOS impact ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable

from sqlalchemy import Select, and_, desc, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from src.db.models.esg_greenos import EsgImpactLedgerModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.observability.logging.logger import logger
from src.orchestration.esg.greenos.services.errors import LedgerIntegrityError


SessionFactory = Callable[[], object]


@dataclass(frozen=True)
class ImpactLedgerInsert:
    """Insert payload for a new ledger record."""

    trip_id: str
    user_id: str
    vehicle_id: str
    country_code: str
    geo_hash: str
    distance_km: float
    co2_avoided_kg: float
    thermal_factor_local: float
    ev_factor_local: float
    model_version: str
    event_hash: str
    checksum: str
    signature: str
    signature_algorithm: str
    key_version: str
    asym_signature: str
    asym_algorithm: str
    asym_key_version: str
    correlation_id: str
    event_timestamp: datetime
    confidence_score: int | None = None
    integrity_index: int | None = None
    anomaly_flags: list[str] | None = None
    aoq_status: str | None = None
    explanation: dict[str, object] | None = None


class ImpactLedgerRepository:
    """SQL persistence for immutable impact records."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or get_session_local()
        Base.metadata.create_all(bind=get_engine(), tables=[EsgImpactLedgerModel.__table__], checkfirst=True)

    @property
    def session_factory(self) -> SessionFactory:
        return self._session_factory

    def create_or_get(self, payload: ImpactLedgerInsert) -> tuple[EsgImpactLedgerModel, bool]:
        """Insert a ledger row or return existing row for idempotent key."""
        with self._session_factory() as session:
            record, idempotent = self.create_or_get_in_session(session=session, payload=payload)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record, idempotent

    def create_or_get_in_session(self, *, session, payload: ImpactLedgerInsert) -> tuple[EsgImpactLedgerModel, bool]:
        """Insert a ledger row in an existing transaction or return idempotent row."""
        existing = self._find_by_trip_model(
            session=session,
            trip_id=payload.trip_id,
            model_version=payload.model_version,
        )
        if existing is not None:
            return existing, True

        values = self._to_insert_values(payload)
        inserted = self._insert_if_absent(session=session, values=values)
        record = self._find_by_trip_model(
            session=session,
            trip_id=payload.trip_id,
            model_version=payload.model_version,
        )
        if record is not None:
            if not inserted:
                logger.warning(
                    "event=greenos_ledger_race_condition_resolved",
                    trip_id=payload.trip_id,
                    model_version=payload.model_version,
                    correlation_id=payload.correlation_id,
                )
            return record, not inserted
        raise LedgerIntegrityError(f"Failed to insert idempotent ledger record for trip_id={payload.trip_id}")

    @staticmethod
    def _to_insert_values(payload: ImpactLedgerInsert) -> dict[str, object]:
        return {
            "trip_id": payload.trip_id,
            "user_id": payload.user_id,
            "vehicle_id": payload.vehicle_id,
            "country_code": payload.country_code,
            "geo_hash": payload.geo_hash,
            "distance_km": Decimal(str(payload.distance_km)),
            "co2_avoided_kg": Decimal(str(payload.co2_avoided_kg)),
            "thermal_factor_local": Decimal(str(payload.thermal_factor_local)),
            "ev_factor_local": Decimal(str(payload.ev_factor_local)),
            "model_version": payload.model_version,
            "event_hash": payload.event_hash,
            "checksum": payload.checksum,
            "signature": payload.signature,
            "signature_algorithm": payload.signature_algorithm,
            "key_version": payload.key_version,
            "asym_signature": payload.asym_signature,
            "asym_algorithm": payload.asym_algorithm,
            "asym_key_version": payload.asym_key_version,
            "correlation_id": payload.correlation_id,
            "event_timestamp": payload.event_timestamp,
            "confidence_score": payload.confidence_score,
            "integrity_index": payload.integrity_index,
            "anomaly_flags": payload.anomaly_flags,
            "aoq_status": payload.aoq_status,
            "explanation": payload.explanation,
        }

    def _insert_if_absent(self, *, session, values: dict[str, object]) -> bool:
        bind = session.get_bind()
        dialect = bind.dialect.name if bind is not None else ""
        if dialect == "postgresql":
            stmt = (
                pg_insert(EsgImpactLedgerModel)
                .values(**values)
                .on_conflict_do_nothing(constraint="uq_esg_impact_trip_model")
            )
            return bool(session.execute(stmt).rowcount)
        if dialect == "sqlite":
            stmt = (
                sqlite_insert(EsgImpactLedgerModel)
                .values(**values)
                .on_conflict_do_nothing(index_elements=["trip_id", "model_version"])
            )
            return bool(session.execute(stmt).rowcount)

        record = EsgImpactLedgerModel(**values)
        try:
            session.add(record)
            session.flush()
            return True
        except IntegrityError as exc:
            raise LedgerIntegrityError("Failed to insert idempotent ledger record") from exc

    def get_by_trip_id(self, trip_id: str, model_version: str | None = None) -> EsgImpactLedgerModel | None:
        """Fetch one impact record by trip (latest if multiple model versions)."""
        with self._session_factory() as session:
            stmt: Select[tuple[EsgImpactLedgerModel]] = select(EsgImpactLedgerModel).where(
                EsgImpactLedgerModel.trip_id == trip_id
            )
            if model_version is not None:
                stmt = stmt.where(EsgImpactLedgerModel.model_version == model_version)
            stmt = stmt.order_by(desc(EsgImpactLedgerModel.created_at)).limit(1)
            return session.execute(stmt).scalar_one_or_none()

    def list_recent_by_user(self, *, user_id: str, limit: int = 50) -> list[EsgImpactLedgerModel]:
        """Return recent ledger records for one user in reverse chronological order."""
        with self._session_factory() as session:
            stmt: Select[tuple[EsgImpactLedgerModel]] = (
                select(EsgImpactLedgerModel)
                .where(EsgImpactLedgerModel.user_id == user_id)
                .order_by(
                    EsgImpactLedgerModel.event_timestamp.desc(),
                    EsgImpactLedgerModel.created_at.desc(),
                )
                .limit(limit)
            )
            return list(session.execute(stmt).scalars().all())

    def aggregate_window(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        country_code: str | None = None,
        session=None,
    ) -> tuple[int, Decimal, Decimal]:
        """Return count, total distance, total CO2 for an audit window."""
        if session is not None:
            return self._aggregate_window_with_session(
                session=session,
                window_start=window_start,
                window_end=window_end,
                country_code=country_code,
            )
        with self._session_factory() as scoped_session:
            return self._aggregate_window_with_session(
                session=scoped_session,
                window_start=window_start,
                window_end=window_end,
                country_code=country_code,
            )

    def list_window(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        country_code: str | None = None,
        session=None,
    ) -> list[EsgImpactLedgerModel]:
        """List ledger rows inside a time window in deterministic order."""
        if session is not None:
            return self._list_window_with_session(
                session=session,
                window_start=window_start,
                window_end=window_end,
                country_code=country_code,
            )
        with self._session_factory() as scoped_session:
            return self._list_window_with_session(
                session=scoped_session,
                window_start=window_start,
                window_end=window_end,
                country_code=country_code,
            )

    def _aggregate_window_with_session(
        self,
        *,
        session,
        window_start: datetime,
        window_end: datetime,
        country_code: str | None,
    ) -> tuple[int, Decimal, Decimal]:
        conditions = [
            EsgImpactLedgerModel.event_timestamp >= window_start,
            EsgImpactLedgerModel.event_timestamp <= window_end,
        ]
        if country_code is not None:
            conditions.append(EsgImpactLedgerModel.country_code == country_code)

        stmt: Select[tuple[EsgImpactLedgerModel]] = (
            select(EsgImpactLedgerModel)
            .where(and_(*conditions))
            .order_by(EsgImpactLedgerModel.event_timestamp.asc())
        )
        rows = list(session.execute(stmt).scalars().all())
        trips_count = len(rows)
        total_distance = sum((row.distance_km for row in rows), Decimal("0"))
        total_co2 = sum((row.co2_avoided_kg for row in rows), Decimal("0"))
        return trips_count, total_distance, total_co2

    def _list_window_with_session(
        self,
        *,
        session,
        window_start: datetime,
        window_end: datetime,
        country_code: str | None,
    ) -> list[EsgImpactLedgerModel]:
        conditions = [
            EsgImpactLedgerModel.event_timestamp >= window_start,
            EsgImpactLedgerModel.event_timestamp <= window_end,
        ]
        if country_code is not None:
            conditions.append(EsgImpactLedgerModel.country_code == country_code)
        stmt: Select[tuple[EsgImpactLedgerModel]] = (
            select(EsgImpactLedgerModel)
            .where(and_(*conditions))
            .order_by(
                EsgImpactLedgerModel.event_timestamp.asc(),
                EsgImpactLedgerModel.trip_id.asc(),
                EsgImpactLedgerModel.model_version.asc(),
                EsgImpactLedgerModel.created_at.asc(),
            )
        )
        return list(session.execute(stmt).scalars().all())

    def _find_by_trip_model(self, *, session, trip_id: str, model_version: str) -> EsgImpactLedgerModel | None:
        stmt = (
            select(EsgImpactLedgerModel)
            .where(
                and_(
                    EsgImpactLedgerModel.trip_id == trip_id,
                    EsgImpactLedgerModel.model_version == model_version,
                )
            )
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()
