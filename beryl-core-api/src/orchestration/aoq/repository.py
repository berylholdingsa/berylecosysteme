"""Persistence layer for AOQ domain."""

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.models.aoq import (
    AoqAuditTrailModel,
    AoqDecisionModel,
    AoqLedgerEntryModel,
    AoqRuleModel,
    AoqSignalModel,
)
from src.db.sqlalchemy import SessionLocal
from src.observability.logger import logger


class AoqRepository:
    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _coerce_user_id(user_id: str | UUID) -> UUID:
        if isinstance(user_id, UUID):
            return user_id
        return UUID(str(user_id))

    def create_signal(self, user_id: str | UUID, source: str, payload: dict) -> AoqSignalModel:
        session = self._session_factory()
        try:
            normalized_user_id = self._coerce_user_id(user_id)
            signal = AoqSignalModel(user_id=str(normalized_user_id), source=source, payload=payload)
            session.add(signal)
            session.commit()
            session.refresh(signal)
            return signal
        except (IntegrityError, SQLAlchemyError) as exc:
            session.rollback()
            logger.exception(
                (
                    "event=aoq_create_signal_sql_error user_id=%s source=%s error_type=%s "
                    "statement=%s params=%s orig=%s"
                ),
                user_id,
                source,
                exc.__class__.__name__,
                getattr(exc, "statement", None),
                getattr(exc, "params", None),
                getattr(exc, "orig", exc),
            )
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_signal(self, signal_id: UUID) -> AoqSignalModel | None:
        with self._session_factory() as session:
            stmt = select(AoqSignalModel).where(AoqSignalModel.id == signal_id)
            return session.execute(stmt).scalar_one_or_none()

    def get_active_rule(self) -> AoqRuleModel | None:
        with self._session_factory() as session:
            stmt = (
                select(AoqRuleModel)
                .where(AoqRuleModel.active.is_(True))
                .order_by(AoqRuleModel.updated_at.desc())
            )
            return session.execute(stmt).scalar_one_or_none()

    def list_rules(self) -> list[AoqRuleModel]:
        with self._session_factory() as session:
            stmt = select(AoqRuleModel).order_by(AoqRuleModel.updated_at.desc())
            return list(session.execute(stmt).scalars().all())

    def create_rule(self, data: dict) -> AoqRuleModel:
        with self._session_factory() as session:
            if data.get("active", True):
                session.execute(update(AoqRuleModel).values(active=False))

            rule = AoqRuleModel(
                name=data["name"],
                threshold=data["threshold"],
                weights={
                    "fintech": data["weight_fintech"],
                    "mobility": data["weight_mobility"],
                    "esg": data["weight_esg"],
                    "social": data["weight_social"],
                },
                active=data.get("active", True),
            )
            session.add(rule)
            session.commit()
            session.refresh(rule)
            return rule

    def create_decision(
        self,
        user_id: str | UUID,
        signal_id: UUID,
        rule_id: UUID,
        score: float,
        threshold: float,
        decision: str,
        rationale: str,
        input_payload: dict,
        impact_type: str,
        audit_payload: dict,
        audit_signature: str,
    ) -> AoqDecisionModel:
        session = self._session_factory()
        try:
            normalized_user_id = self._coerce_user_id(user_id)
            aoq_decision = AoqDecisionModel(
                user_id=str(normalized_user_id),
                signal_id=signal_id,
                rule_id=rule_id,
                score=score,
                threshold=threshold,
                decision=decision,
                rationale=rationale,
                input_payload=input_payload,
            )
            session.add(aoq_decision)
            session.flush()

            ledger_entry = AoqLedgerEntryModel(
                decision_id=aoq_decision.id,
                user_id=str(normalized_user_id),
                impact_type=impact_type,
                score=score,
                decision=decision,
            )
            session.add(ledger_entry)

            audit_trail = AoqAuditTrailModel(
                event_type="AOQ_DECISION_CREATED",
                entity_id=str(aoq_decision.id),
                payload=audit_payload,
                signature=audit_signature,
            )
            session.add(audit_trail)

            session.commit()
            session.refresh(aoq_decision)
            return aoq_decision
        except (IntegrityError, SQLAlchemyError) as exc:
            session.rollback()
            logger.exception(
                (
                    "event=aoq_create_decision_sql_error user_id=%s signal_id=%s rule_id=%s "
                    "error_type=%s statement=%s params=%s orig=%s"
                ),
                user_id,
                signal_id,
                rule_id,
                exc.__class__.__name__,
                getattr(exc, "statement", None),
                getattr(exc, "params", None),
                getattr(exc, "orig", exc),
            )
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_decision(self, decision_id: UUID) -> AoqDecisionModel | None:
        with self._session_factory() as session:
            stmt = select(AoqDecisionModel).where(AoqDecisionModel.id == decision_id)
            return session.execute(stmt).scalar_one_or_none()

    def list_audit_trail(self, entity_id: str) -> list[AoqAuditTrailModel]:
        with self._session_factory() as session:
            stmt = (
                select(AoqAuditTrailModel)
                .where(AoqAuditTrailModel.entity_id == entity_id)
                .order_by(AoqAuditTrailModel.created_at.desc())
            )
            return list(session.execute(stmt).scalars().all())

    def count_active_rules(self) -> int:
        with self._session_factory() as session:
            stmt = select(func.count()).select_from(AoqRuleModel).where(AoqRuleModel.active.is_(True))
            return int(session.execute(stmt).scalar_one())
