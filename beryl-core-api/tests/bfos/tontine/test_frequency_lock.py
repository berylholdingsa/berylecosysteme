from __future__ import annotations

from decimal import Decimal
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.tontine.tontine_engine import TontineEngine
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.tontine import (
    TontineCycleModel,
    TontineGroupModel,
    TontineMemberModel,
    TontineVoteModel,
    TontineWithdrawRequestModel,
)
from src.db.sqlalchemy import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AuditChainEventModel.__table__,
            IdempotencyKeyModel.__table__,
            LedgerUserModel.__table__,
            LedgerAccountModel.__table__,
            LedgerEntryModel.__table__,
            TontineGroupModel.__table__,
            TontineMemberModel.__table__,
            TontineCycleModel.__table__,
            TontineWithdrawRequestModel.__table__,
            TontineVoteModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_frequency_change_rejected_when_cycle_active() -> None:
    factory = _session_factory()
    engine = TontineEngine(session_factory=factory)

    created = engine.create_tontine(
        community_group_id="community-lock",
        created_by="member-lock",
        contribution_amount=Decimal("100.00"),
        frequency_type="WEEKLY",
        security_code="44444",
        max_members=5,
        idempotency_key="idem-create-lock",
        correlation_id="corr-create-lock",
    )
    engine.contribute(
        tontine_id=created["tontine_id"],
        user_id="member-lock",
        amount=Decimal("100.00"),
        idempotency_key="idem-contrib-lock",
        correlation_id="corr-contrib-lock",
    )

    with pytest.raises(ValueError, match="immutable"):
        engine.update_frequency(
            tontine_id=created["tontine_id"],
            requested_frequency="MONTHLY",
            actor_id="member-lock",
            idempotency_key="idem-update-lock",
            correlation_id="corr-update-lock",
        )

    with factory() as session:
        group = session.execute(
            select(TontineGroupModel).where(TontineGroupModel.id == uuid.UUID(created["tontine_id"]))
        ).scalar_one()
        rejected_events = list(
            session.execute(
                select(AuditChainEventModel).where(AuditChainEventModel.action == "TONTINE_FREQUENCY_UPDATE_REJECTED")
            ).scalars().all()
        )

    assert group.frequency_type == "WEEKLY"
    assert len(rejected_events) == 1
