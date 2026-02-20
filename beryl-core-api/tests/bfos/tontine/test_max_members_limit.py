from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
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


def test_max_members_limit_enforced() -> None:
    factory = _session_factory()
    engine = TontineEngine(session_factory=factory)

    created = engine.create_tontine(
        community_group_id="community-g1",
        created_by="member-1",
        contribution_amount=Decimal("100.00"),
        frequency_type="WEEKLY",
        security_code="12345",
        max_members=2,
        idempotency_key="idem-create-max-members",
        correlation_id="corr-create-max-members",
    )
    assert created["member_count"] == 1

    joined = engine.join_tontine(
        tontine_id=created["tontine_id"],
        user_id="member-2",
        idempotency_key="idem-join-member-2",
        correlation_id="corr-join-member-2",
    )
    assert joined["member_count"] == 2

    with pytest.raises(ValueError, match="max members limit reached"):
        engine.join_tontine(
            tontine_id=created["tontine_id"],
            user_id="member-3",
            idempotency_key="idem-join-member-3",
            correlation_id="corr-join-member-3",
        )
