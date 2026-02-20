"""AOQ domain service with persistent rule/signal/decision handling."""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from uuid import UUID
import uuid

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.config.settings import settings
from src.db.models.aoq import (
    AoqAuditTrailModel,
    AoqDecisionModel,
    AoqLedgerEntryModel,
    AoqRuleModel,
    AoqSignalModel,
)
from src.db.sqlalchemy import Base, get_engine
from src.observability.logger import logger
from src.observability.metrics.prometheus import metrics
from src.orchestration.aoq.repository import AoqRepository


class AoqError(Exception):
    """Base AOQ domain exception."""


class AoqNotFoundError(AoqError):
    """Raised when an AOQ entity is not found."""


class AoqValidationError(AoqError):
    """Raised when AOQ payload validation fails."""


@dataclass(slots=True)
class AoqDecisionResult:
    decision_id: UUID
    signal_id: UUID
    rule_id: UUID
    user_id: str
    score: float
    threshold: float
    decision: str
    rationale: str
    created_at: object


class AoqService:
    def __init__(self, repository: AoqRepository | None = None) -> None:
        self._repository = repository or AoqRepository()
        self._init_aoq_tables()

    def _init_aoq_tables(self) -> None:
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[
                    AoqRuleModel.__table__,
                    AoqSignalModel.__table__,
                    AoqDecisionModel.__table__,
                    AoqLedgerEntryModel.__table__,
                    AoqAuditTrailModel.__table__,
                ],
                checkfirst=True,
            )
        except Exception as exc:
            logger.warning("event=aoq_init_tables_skipped reason=%s", exc)

    def create_signal(self, user_id: str, source: str, payload: dict) -> AoqSignalModel:
        try:
            signal = self._repository.create_signal(user_id=user_id, source=source, payload=payload)
            logger.info(
                "event=aoq_signal_created signal_id=%s user_id=%s source=%s",
                signal.id,
                user_id,
                source,
            )
            return signal
        except ValueError as exc:
            raise AoqValidationError(f"invalid user_id UUID: {user_id}") from exc
        except SQLAlchemyError as exc:
            logger.exception(
                "event=aoq_signal_sqlalchemy_error user_id=%s source=%s error=%s",
                user_id,
                source,
                str(exc),
            )
            raise

    def list_rules(self) -> list[AoqRuleModel]:
        return self._repository.list_rules()

    def create_rule(self, rule_payload: dict) -> AoqRuleModel:
        try:
            rule = self._repository.create_rule(rule_payload)
        except IntegrityError as exc:
            logger.exception(
                "event=aoq_rule_integrity_error name=%s payload=%s error=%s",
                rule_payload.get("name"),
                rule_payload,
                str(exc),
            )
            raise AoqValidationError("rule name must be unique") from exc
        except SQLAlchemyError as exc:
            logger.exception(
                "event=aoq_rule_sql_error name=%s payload=%s error=%s",
                rule_payload.get("name"),
                rule_payload,
                str(exc),
            )
            raise AoqValidationError("invalid AOQ rule persistence payload") from exc

        logger.info(
            "event=aoq_rule_created rule_id=%s name=%s threshold=%s active=%s version=%s",
            rule.id,
            rule.name,
            rule.threshold,
            rule.active,
            rule.version,
        )
        return rule

    def get_decision(self, decision_id: UUID) -> AoqDecisionModel:
        decision = self._repository.get_decision(decision_id)
        if decision is None:
            raise AoqNotFoundError(f"decision {decision_id} not found")
        return decision

    def get_audit_trail(self, entity_id: str) -> list[AoqAuditTrailModel]:
        return self._repository.list_audit_trail(entity_id)

    def compute_decision(
        self,
        user_id: str,
        signal_id: UUID | None,
        features_payload: dict | None,
        metadata: dict | None,
    ) -> AoqDecisionResult:
        started_at = time.perf_counter()
        active_rule = self._repository.get_active_rule()
        if active_rule is None:
            active_rule = self.create_rule(
                {
                    "name": f"default-{uuid.uuid4().hex[:8]}",
                    "threshold": 60.0,
                    "weight_fintech": 0.35,
                    "weight_mobility": 0.25,
                    "weight_esg": 0.25,
                    "weight_social": 0.15,
                    "active": True,
                }
            )

        signal = None
        if signal_id is not None:
            signal = self._repository.get_signal(signal_id)
            if signal is None:
                raise AoqNotFoundError(f"signal {signal_id} not found")
            signal_payload = signal.payload
        else:
            if not features_payload:
                raise AoqValidationError("features must be provided when signal_id is missing")
            merged_payload = {
                "features": features_payload,
                "metadata": metadata or {},
            }
            signal = self.create_signal(user_id=user_id, source="decision", payload=merged_payload)
            signal_payload = merged_payload

        features = signal_payload.get("features")
        if not isinstance(features, dict):
            raise AoqValidationError("signal payload must contain a features object")

        score = self._weighted_score(features=features, rule=active_rule)
        decision_value = "APPROVE" if score > active_rule.threshold else "REJECT"
        impact_type = self._resolve_impact_type(features=features, metadata=metadata)
        rationale = (
            f"score={score:.2f} threshold={active_rule.threshold:.2f} "
            f"weights={active_rule.weight_fintech:.2f}/{active_rule.weight_mobility:.2f}/"
            f"{active_rule.weight_esg:.2f}/{active_rule.weight_social:.2f}"
        )
        audit_payload = {
            "user_id": user_id,
            "impact_type": impact_type,
            "score": score,
            "decision": decision_value,
            "threshold": active_rule.threshold,
        }
        audit_signature = self._sign_payload(audit_payload)

        try:
            persisted = self._repository.create_decision(
                user_id=user_id,
                signal_id=signal.id,
                rule_id=active_rule.id,
                score=score,
                threshold=active_rule.threshold,
                decision=decision_value,
                rationale=rationale,
                input_payload=signal_payload,
                impact_type=impact_type,
                audit_payload=audit_payload,
                audit_signature=audit_signature,
            )
        except ValueError as exc:
            raise AoqValidationError(f"invalid user_id UUID: {user_id}") from exc
        except SQLAlchemyError as exc:
            logger.exception(
                (
                    "event=aoq_decision_sqlalchemy_error user_id=%s signal_id=%s rule_id=%s "
                    "error=%s"
                ),
                user_id,
                signal.id if signal else None,
                active_rule.id if active_rule else None,
                str(exc),
            )
            raise
        latency_seconds = time.perf_counter() - started_at
        active_rules = self._repository.count_active_rules()
        metrics.record_aoq_decision(
            decision=decision_value,
            latency_seconds=latency_seconds,
            active_rules=active_rules,
        )

        logger.info(
            (
                "event=aoq_decision_created decision_id=%s signal_id=%s user_id=%s "
                "score=%.2f threshold=%.2f decision=%s impact_type=%s latency_seconds=%.6f"
            ),
            persisted.id,
            signal.id,
            user_id,
            score,
            active_rule.threshold,
            decision_value,
            impact_type,
            latency_seconds,
        )

        return AoqDecisionResult(
            decision_id=persisted.id,
            signal_id=persisted.signal_id,
            rule_id=persisted.rule_id,
            user_id=persisted.user_id,
            score=persisted.score,
            threshold=persisted.threshold,
            decision=persisted.decision,
            rationale=persisted.rationale,
            created_at=persisted.created_at,
        )

    def _weighted_score(self, features: dict, rule: AoqRuleModel) -> float:
        fintech_score = float(features.get("fintech_score", 0.0))
        mobility_score = float(features.get("mobility_score", 0.0))
        esg_score = float(features.get("esg_score", 0.0))
        social_score = float(features.get("social_score", 0.0))

        for name, value in {
            "fintech_score": fintech_score,
            "mobility_score": mobility_score,
            "esg_score": esg_score,
            "social_score": social_score,
        }.items():
            if value < 0 or value > 100:
                raise AoqValidationError(f"{name} must be between 0 and 100")

        weighted = (
            fintech_score * rule.weight_fintech
            + mobility_score * rule.weight_mobility
            + esg_score * rule.weight_esg
            + social_score * rule.weight_social
        )
        return round(weighted, 2)

    def _resolve_impact_type(self, features: dict, metadata: dict | None) -> str:
        allowed = {"credit", "pricing", "esg", "matching"}
        if metadata:
            for key in ("impact_type", "use_case", "scenario"):
                value = metadata.get(key)
                if isinstance(value, str):
                    normalized = value.strip().lower()
                    if normalized in allowed:
                        return normalized
        dominant = max(
            (
                ("credit", float(features.get("fintech_score", 0.0))),
                ("pricing", float(features.get("mobility_score", 0.0))),
                ("esg", float(features.get("esg_score", 0.0))),
                ("matching", float(features.get("social_score", 0.0))),
            ),
            key=lambda item: item[1],
        )
        return dominant[0]

    def _sign_payload(self, payload: dict) -> str:
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hmac.new(
            settings.audit_secret_key.encode("utf-8"),
            canonical_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
