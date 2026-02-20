from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.fee_engine import FeeEngine
from src.bfos.fx_engine import FxEngine
from src.bfos.revenue_engine import RevenueEngine
from src.core.audit.service import AuditService
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.fx_rates import FxRateModel, FxTransactionModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.revenue import RevenueRecordModel
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
            RevenueRecordModel.__table__,
            FxRateModel.__table__,
            FxTransactionModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_bfos_integrity_double_entry_audit_signature_idempotency() -> None:
    factory = _session_factory()
    audit = AuditService(session_factory=factory)
    revenue = RevenueEngine(session_factory=factory)
    fx = FxEngine(session_factory=factory, linked_revenue_engine=revenue)
    fees = FeeEngine(session_factory=factory)

    with factory() as session:
        with session.begin():
            fee = fees.calculate_internal_transfer_fee(
                Decimal("500.00"),
                session=session,
                actor_id="actor-1",
                correlation_id="corr-fee",
                transaction_id="tx-fee-1",
            )
            revenue.record_revenue(
                source="internal_transfer_fee",
                amount=fee.fee_amount,
                currency="XOF",
                transaction_id="tx-rev-core",
                actor_id="actor-1",
                correlation_id="corr-rev",
                session=session,
            )

    fx_first = fx.record_fx_transaction(
        Decimal("50.00"),
        transaction_id="tx-fx-core",
        fee_payer="receiver",
        actor_id="actor-1",
        correlation_id="corr-fx",
    )
    fx_second = fx.record_fx_transaction(
        Decimal("50.00"),
        transaction_id="tx-fx-core",
        fee_payer="receiver",
        actor_id="actor-1",
        correlation_id="corr-fx",
    )

    assert fee.fee_amount > Decimal("0.00")
    assert fx_first["idempotent"] is False
    assert fx_second["idempotent"] is True

    with factory() as session:
        rev_entries = list(
            session.execute(select(LedgerEntryModel).where(LedgerEntryModel.reference == "tx-rev-core")).scalars().all()
        )
        assert len(rev_entries) == 2
        assert {entry.direction for entry in rev_entries} == {"DEBIT", "CREDIT"}
        assert rev_entries[0].amount == rev_entries[1].amount

    _, issues = audit.verify_integrity()
    invalid_rows = [issue for issue in issues if issue.startswith("invalid_signature_or_hash")]
    assert not invalid_rows, invalid_rows
