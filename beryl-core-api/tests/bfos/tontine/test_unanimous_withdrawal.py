from __future__ import annotations

from decimal import Decimal

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


def test_withdraw_requires_unanimous_vote() -> None:
    factory = _session_factory()
    engine = TontineEngine(session_factory=factory)

    created = engine.create_tontine(
        community_group_id="community-g2",
        created_by="member-a",
        contribution_amount=Decimal("100.00"),
        frequency_type="WEEKLY",
        security_code="55555",
        max_members=2,
        idempotency_key="idem-create-unanimous",
        correlation_id="corr-create-unanimous",
    )
    engine.join_tontine(
        tontine_id=created["tontine_id"],
        user_id="member-b",
        idempotency_key="idem-join-unanimous",
        correlation_id="corr-join-unanimous",
    )

    engine.contribute(
        tontine_id=created["tontine_id"],
        user_id="member-a",
        amount=Decimal("100.00"),
        idempotency_key="idem-contrib-a",
        correlation_id="corr-contrib-a",
    )
    engine.contribute(
        tontine_id=created["tontine_id"],
        user_id="member-b",
        amount=Decimal("100.00"),
        idempotency_key="idem-contrib-b",
        correlation_id="corr-contrib-b",
    )

    request = engine.request_withdraw(
        tontine_id=created["tontine_id"],
        requested_by="member-a",
        amount=Decimal("100.00"),
        security_code="55555",
        idempotency_key="idem-withdraw-request",
        correlation_id="corr-withdraw-request",
    )
    assert request["withdraw_status"] == "PENDING"

    first_vote = engine.vote_withdraw(
        tontine_id=created["tontine_id"],
        withdraw_request_id=request["withdraw_request_id"],
        user_id="member-a",
        approved=True,
        security_code="55555",
        idempotency_key="idem-vote-a",
        correlation_id="corr-vote-a",
    )
    assert first_vote["status"] == "PENDING"

    second_vote = engine.vote_withdraw(
        tontine_id=created["tontine_id"],
        withdraw_request_id=request["withdraw_request_id"],
        user_id="member-b",
        approved=True,
        security_code="55555",
        idempotency_key="idem-vote-b",
        correlation_id="corr-vote-b",
    )
    assert second_vote["status"] == "EXECUTED"
    assert second_vote["executed"] is True

    rejected_request = engine.request_withdraw(
        tontine_id=created["tontine_id"],
        requested_by="member-a",
        amount=Decimal("20.00"),
        security_code="55555",
        idempotency_key="idem-withdraw-request-2",
        correlation_id="corr-withdraw-request-2",
    )
    rejected_vote = engine.vote_withdraw(
        tontine_id=created["tontine_id"],
        withdraw_request_id=rejected_request["withdraw_request_id"],
        user_id="member-a",
        approved=False,
        security_code="55555",
        idempotency_key="idem-vote-reject",
        correlation_id="corr-vote-reject",
    )
    assert rejected_vote["status"] == "REJECTED"
