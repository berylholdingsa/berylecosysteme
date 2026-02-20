"""Repository for versioned GreenOS MRV methodologies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import UUID

from sqlalchemy import Select, desc, select
from sqlalchemy.exc import IntegrityError

from src.db.models.esg_greenos import EsgMrvMethodologyModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.orchestration.esg.greenos.services.errors import (
    MrvMethodologyConflictError,
    MrvMethodologyNotFoundError,
)


SessionFactory = Callable[[], object]


@dataclass(frozen=True)
class MrvMethodologyInsert:
    """Insert payload for MRV methodology versions."""

    methodology_version: str
    baseline_description: str
    emission_factor_source: str
    thermal_factor_reference: str
    ev_factor_reference: str
    calculation_formula: str
    geographic_scope: str
    model_version: str
    status: str = "ACTIVE"


class MrvMethodologyRepository:
    """Persistence adapter for MRV methodology versions."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or get_session_local()
        Base.metadata.create_all(bind=get_engine(), tables=[EsgMrvMethodologyModel.__table__], checkfirst=True)

    @property
    def session_factory(self) -> SessionFactory:
        return self._session_factory

    def create(self, payload: MrvMethodologyInsert) -> EsgMrvMethodologyModel:
        with self._session_factory() as session:
            record = self.create_in_session(session=session, payload=payload)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def create_in_session(self, *, session, payload: MrvMethodologyInsert) -> EsgMrvMethodologyModel:
        if payload.status == "ACTIVE":
            active = self._get_active_in_session(session=session)
            if active is not None:
                raise MrvMethodologyConflictError(
                    f"Active methodology already exists: {active.methodology_version}"
                )

        record = EsgMrvMethodologyModel(
            methodology_version=payload.methodology_version,
            baseline_description=payload.baseline_description,
            emission_factor_source=payload.emission_factor_source,
            thermal_factor_reference=payload.thermal_factor_reference,
            ev_factor_reference=payload.ev_factor_reference,
            calculation_formula=payload.calculation_formula,
            geographic_scope=payload.geographic_scope,
            model_version=payload.model_version,
            status=payload.status,
        )
        session.add(record)
        try:
            session.flush()
        except IntegrityError as exc:
            raise MrvMethodologyConflictError("Unable to create MRV methodology version") from exc
        return record

    def get_active(self) -> EsgMrvMethodologyModel | None:
        with self._session_factory() as session:
            return self._get_active_in_session(session=session)

    def get_by_version(self, *, version: str) -> EsgMrvMethodologyModel | None:
        with self._session_factory() as session:
            stmt: Select[tuple[EsgMrvMethodologyModel]] = (
                select(EsgMrvMethodologyModel)
                .where(EsgMrvMethodologyModel.methodology_version == version)
                .order_by(desc(EsgMrvMethodologyModel.created_at))
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, *, methodology_id: UUID) -> EsgMrvMethodologyModel | None:
        with self._session_factory() as session:
            stmt: Select[tuple[EsgMrvMethodologyModel]] = (
                select(EsgMrvMethodologyModel)
                .where(EsgMrvMethodologyModel.id == methodology_id)
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none()

    def set_status(self, *, version: str, status: str) -> EsgMrvMethodologyModel:
        with self._session_factory() as session:
            with session.begin():
                record = self._get_by_version_in_session(session=session, version=version)
                if record is None:
                    raise MrvMethodologyNotFoundError(f"Methodology version not found: {version}")
                if status == "ACTIVE":
                    active = self._get_active_in_session(session=session)
                    if active is not None and active.id != record.id:
                        active.status = "DEPRECATED"
                record.status = status
            session.refresh(record)
            session.expunge(record)
            return record

    @staticmethod
    def _get_active_in_session(*, session) -> EsgMrvMethodologyModel | None:
        stmt: Select[tuple[EsgMrvMethodologyModel]] = (
            select(EsgMrvMethodologyModel)
            .where(EsgMrvMethodologyModel.status == "ACTIVE")
            .order_by(desc(EsgMrvMethodologyModel.created_at))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def _get_by_version_in_session(*, session, version: str) -> EsgMrvMethodologyModel | None:
        stmt: Select[tuple[EsgMrvMethodologyModel]] = (
            select(EsgMrvMethodologyModel)
            .where(EsgMrvMethodologyModel.methodology_version == version)
            .order_by(desc(EsgMrvMethodologyModel.created_at))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

