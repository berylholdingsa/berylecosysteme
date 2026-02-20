"""Repository layer for GreenOS MRV exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import Select, and_, desc, select
from sqlalchemy.exc import IntegrityError

from src.db.models.esg_greenos import EsgMrvExportModel, EsgMrvMethodologyModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.orchestration.esg.greenos.services.errors import MrvExportAlreadyExistsError


SessionFactory = Callable[[], object]


@dataclass(frozen=True)
class MrvExportInsert:
    """Insert payload for persisted MRV exports."""

    methodology_id: UUID
    period_start: datetime
    period_end: datetime
    total_co2_avoided: Decimal
    total_distance: Decimal
    methodology_version: str
    methodology_hash: str
    baseline_reference: str
    emission_factor_source: str
    verification_hash: str
    signature: str
    signature_algorithm: str
    key_version: str
    asym_signature: str
    asym_algorithm: str
    asym_key_version: str
    payload: dict[str, Any]
    status: str
    confidence_score: int | None = None
    integrity_index: int | None = None
    anomaly_flags: list[str] | None = None
    aoq_status: str | None = None
    explanation: dict[str, Any] | None = None


class MrvExportRepository:
    """Storage adapter for materialized MRV export documents."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or get_session_local()
        Base.metadata.create_all(
            bind=get_engine(),
            tables=[EsgMrvMethodologyModel.__table__, EsgMrvExportModel.__table__],
            checkfirst=True,
        )

    @property
    def session_factory(self) -> SessionFactory:
        return self._session_factory

    def create(self, payload: MrvExportInsert) -> EsgMrvExportModel:
        with self._session_factory() as session:
            record = self.create_in_session(session=session, payload=payload)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def create_in_session(self, *, session, payload: MrvExportInsert) -> EsgMrvExportModel:
        if self._get_by_period_in_session(
            session=session,
            period_start=payload.period_start,
            period_end=payload.period_end,
        ) is not None:
            raise MrvExportAlreadyExistsError("MRV export already exists for this period")

        record = EsgMrvExportModel(
            methodology_id=payload.methodology_id,
            period_start=payload.period_start,
            period_end=payload.period_end,
            total_co2_avoided=payload.total_co2_avoided,
            total_distance=payload.total_distance,
            methodology_version=payload.methodology_version,
            methodology_hash=payload.methodology_hash,
            baseline_reference=payload.baseline_reference,
            emission_factor_source=payload.emission_factor_source,
            verification_hash=payload.verification_hash,
            signature=payload.signature,
            signature_algorithm=payload.signature_algorithm,
            key_version=payload.key_version,
            asym_signature=payload.asym_signature,
            asym_algorithm=payload.asym_algorithm,
            asym_key_version=payload.asym_key_version,
            payload=payload.payload,
            status=payload.status,
            confidence_score=payload.confidence_score,
            integrity_index=payload.integrity_index,
            anomaly_flags=payload.anomaly_flags,
            aoq_status=payload.aoq_status,
            explanation=payload.explanation,
        )
        session.add(record)
        try:
            session.flush()
        except IntegrityError as exc:
            raise MrvExportAlreadyExistsError("MRV export already exists for this period") from exc
        return record

    def get_by_id(self, *, export_id: UUID) -> EsgMrvExportModel | None:
        with self._session_factory() as session:
            stmt: Select[tuple[EsgMrvExportModel]] = (
                select(EsgMrvExportModel)
                .where(EsgMrvExportModel.id == export_id)
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_latest_by_period(self, *, period_start: datetime, period_end: datetime) -> EsgMrvExportModel | None:
        with self._session_factory() as session:
            return self._get_by_period_in_session(
                session=session,
                period_start=period_start,
                period_end=period_end,
            )

    @staticmethod
    def _get_by_period_in_session(*, session, period_start: datetime, period_end: datetime) -> EsgMrvExportModel | None:
        stmt: Select[tuple[EsgMrvExportModel]] = (
            select(EsgMrvExportModel)
            .where(
                and_(
                    EsgMrvExportModel.period_start == period_start,
                    EsgMrvExportModel.period_end == period_end,
                )
            )
            .order_by(desc(EsgMrvExportModel.created_at))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()
