"""Unit tests for AOQ decision side-effects (ledger + audit)."""

import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.db.models.aoq import (
    AoqAuditTrailModel,
    AoqDecisionModel,
    AoqLedgerEntryModel,
    AoqRuleModel,
    AoqSignalModel,
)
from src.db.sqlalchemy import Base
from src.orchestration.aoq.repository import AoqRepository


def test_create_decision_creates_ledger_and_audit(tmp_path):
    db_path = tmp_path / "aoq_decision.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AoqRuleModel.__table__,
            AoqSignalModel.__table__,
            AoqDecisionModel.__table__,
            AoqLedgerEntryModel.__table__,
            AoqAuditTrailModel.__table__,
        ],
        checkfirst=True,
    )

    repository = AoqRepository(session_factory=SessionLocal)

    signal = repository.create_signal(
        user_id="user-1",
        source="mobile",
        payload={"features": {"fintech_score": 80, "mobility_score": 70, "esg_score": 60, "social_score": 90}},
    )
    rule = repository.create_rule(
        {
            "name": f"rule-{uuid.uuid4().hex[:8]}",
            "threshold": 60.0,
            "weight_fintech": 0.35,
            "weight_mobility": 0.25,
            "weight_esg": 0.25,
            "weight_social": 0.15,
            "active": True,
        }
    )

    decision = repository.create_decision(
        user_id="user-1",
        signal_id=signal.id,
        rule_id=rule.id,
        score=72.5,
        threshold=60.0,
        decision="APPROVE",
        rationale="score=72.5 threshold=60",
        input_payload={"features": {"fintech_score": 80}},
        impact_type="credit",
        audit_payload={"user_id": "user-1", "decision": "APPROVE"},
        audit_signature="deadbeef",
    )

    with SessionLocal() as session:
        ledger = session.execute(
            select(AoqLedgerEntryModel).where(AoqLedgerEntryModel.decision_id == decision.id)
        ).scalar_one()
        audit = session.execute(
            select(AoqAuditTrailModel).where(AoqAuditTrailModel.entity_id == str(decision.id))
        ).scalar_one()

        assert ledger.user_id == "user-1"
        assert ledger.impact_type == "credit"
        assert ledger.decision == "APPROVE"
        assert audit.event_type == "AOQ_DECISION_CREATED"
        assert audit.payload["decision"] == "APPROVE"
        assert audit.signature == "deadbeef"
