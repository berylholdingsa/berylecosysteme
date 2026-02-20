from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.tontine.tontine_engine import TontineEngine
from src.core.audit.service import AuditService
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


def test_tontine_ledger_keeps_double_entry_and_audit_chain_integrity() -> None:
    factory = _session_factory()
    engine = TontineEngine(session_factory=factory)
    audit = AuditService(session_factory=factory)

    created = engine.create_tontine(
        community_group_id="community-ledger",
        created_by="ledger-a",
        contribution_amount=Decimal("100.00"),
        frequency_type="WEEKLY",
        security_code="99999",
        max_members=2,
        idempotency_key="idem-create-ledger",
        correlation_id="corr-create-ledger",
    )
    engine.join_tontine(
        tontine_id=created["tontine_id"],
        user_id="ledger-b",
        idempotency_key="idem-join-ledger",
        correlation_id="corr-join-ledger",
    )
    engine.contribute(
        tontine_id=created["tontine_id"],
        user_id="ledger-a",
        amount=Decimal("100.00"),
        idempotency_key="idem-contrib-ledger-a",
        correlation_id="corr-contrib-ledger-a",
    )
    engine.contribute(
        tontine_id=created["tontine_id"],
        user_id="ledger-b",
        amount=Decimal("100.00"),
        idempotency_key="idem-contrib-ledger-b",
        correlation_id="corr-contrib-ledger-b",
    )
    withdraw = engine.request_withdraw(
        tontine_id=created["tontine_id"],
        requested_by="ledger-a",
        amount=Decimal("50.00"),
        security_code="99999",
        idempotency_key="idem-withdraw-ledger",
        correlation_id="corr-withdraw-ledger",
    )
    engine.vote_withdraw(
        tontine_id=created["tontine_id"],
        withdraw_request_id=withdraw["withdraw_request_id"],
        user_id="ledger-a",
        approved=True,
        security_code="99999",
        idempotency_key="idem-vote-ledger-a",
        correlation_id="corr-vote-ledger-a",
    )
    engine.vote_withdraw(
        tontine_id=created["tontine_id"],
        withdraw_request_id=withdraw["withdraw_request_id"],
        user_id="ledger-b",
        approved=True,
        security_code="99999",
        idempotency_key="idem-vote-ledger-b",
        correlation_id="corr-vote-ledger-b",
    )

    with factory() as session:
        entries = list(
            session.execute(
                select(LedgerEntryModel).where(LedgerEntryModel.reference.like("tontine:%"))
            ).scalars().all()
        )

    by_reference: dict[str, list[LedgerEntryModel]] = defaultdict(list)
    for entry in entries:
        by_reference[str(entry.reference)].append(entry)

    assert by_reference, "Expected tontine ledger entries to be present"
    for ref, grouped in by_reference.items():
        assert len(grouped) == 2, f"{ref} does not have exactly two entries"
        assert {entry.direction for entry in grouped} == {"DEBIT", "CREDIT"}
        amounts = {Decimal(str(entry.amount)).quantize(Decimal("0.01")) for entry in grouped}
        assert len(amounts) == 1, f"{ref} has inconsistent debit/credit amount"

    _, issues = audit.verify_integrity()
    invalid_rows = [issue for issue in issues if issue.startswith("invalid_signature_or_hash")]
    assert not invalid_rows, invalid_rows
