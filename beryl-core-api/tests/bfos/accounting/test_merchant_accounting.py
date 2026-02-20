from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.accounting.merchant_accounting_engine import MerchantAccountingEngine
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.fintech import FintechTransactionModel
from src.db.sqlalchemy import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[AuditChainEventModel.__table__, FintechTransactionModel.__table__])
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_merchant_accounting_aggregation_summary_and_cashflow() -> None:
    factory = _session_factory()
    accounting = MerchantAccountingEngine(session_factory=factory)

    now = datetime.now(timezone.utc)
    with factory() as session:
        with session.begin():
            session.add_all(
                [
                    FintechTransactionModel(
                        id=uuid.uuid4(),
                        actor_id="merchant-1",
                        amount=Decimal("1000.00"),
                        currency="XOF",
                        target_account="wallet-sales",
                        status="ACCEPTED",
                        risk_score=Decimal("0"),
                        aml_flagged=False,
                        correlation_id="corr-1",
                        created_at=now - timedelta(days=1),
                    ),
                    FintechTransactionModel(
                        id=uuid.uuid4(),
                        actor_id="merchant-1",
                        amount=Decimal("200.00"),
                        currency="XOF",
                        target_account="expense-office",
                        status="ACCEPTED",
                        risk_score=Decimal("0"),
                        aml_flagged=False,
                        correlation_id="corr-2",
                        created_at=now - timedelta(days=1),
                    ),
                    FintechTransactionModel(
                        id=uuid.uuid4(),
                        actor_id="merchant-1",
                        amount=Decimal("300.00"),
                        currency="XOF",
                        target_account="wallet-sales",
                        status="FAILED",
                        risk_score=Decimal("0"),
                        aml_flagged=False,
                        correlation_id="corr-3",
                        created_at=now - timedelta(days=1),
                    ),
                ]
            )

    result = accounting.aggregate_transactions(
        user_id="merchant-1",
        start_date=(now.date() - timedelta(days=90)),
        end_date=now.date(),
    )

    summary = result["summary"]
    cashflow = result["cashflow"]

    assert Decimal(str(summary["total_sales"])) == Decimal("1000.00")
    assert Decimal(str(summary["total_charges"])) == Decimal("200.00")
    assert Decimal(str(summary["net_result"])) == Decimal("800.00")
    assert Decimal(str(cashflow["inflow"])) == Decimal("1000.00")
    assert Decimal(str(cashflow["outflow"])) == Decimal("200.00")
    assert Decimal(str(cashflow["net_cashflow"])) == Decimal("800.00")

    with factory() as session:
        audits = list(session.execute(select(AuditChainEventModel)).scalars().all())
    assert any(row.action == "BFOS_MERCHANT_ACCOUNTING_AGGREGATED" for row in audits)
