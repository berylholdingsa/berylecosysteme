from __future__ import annotations

from decimal import Decimal

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


def test_tontine_commission_is_1_percent_and_ledgered() -> None:
    factory = _session_factory()
    engine = TontineEngine(session_factory=factory)
    created = engine.create_tontine(
        community_group_id="community-fee",
        created_by="member-fee",
        contribution_amount=Decimal("1000.00"),
        frequency_type="WEEKLY",
        security_code="33333",
        max_members=5,
        idempotency_key="idem-create-fee",
        correlation_id="corr-create-fee",
    )

    contribution = engine.contribute(
        tontine_id=created["tontine_id"],
        user_id="member-fee",
        amount=Decimal("1000.00"),
        idempotency_key="idem-contrib-fee",
        correlation_id="corr-contrib-fee",
    )
    assert Decimal(contribution["fee_amount"]) == Decimal("10.00")

    with factory() as session:
        commission_entries = list(
            session.execute(
                select(LedgerEntryModel).where(LedgerEntryModel.reference.like("%commission%"))
            ).scalars().all()
        )
        fee_audit = list(
            session.execute(
                select(AuditChainEventModel).where(AuditChainEventModel.action == "BFOS_FEE_CALCULATED")
            ).scalars().all()
        )

    assert len(commission_entries) == 2
    assert {entry.direction for entry in commission_entries} == {"DEBIT", "CREDIT"}
    assert all(Decimal(str(entry.amount)) == Decimal("10.00") for entry in commission_entries)
    assert len(fee_audit) >= 1
