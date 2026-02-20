from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.fee_engine import FeeEngine
from src.db.models.audit_chain import AuditChainEventModel
from src.db.sqlalchemy import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[AuditChainEventModel.__table__])
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_fee_engine_calculates_expected_rates_and_audits() -> None:
    factory = _session_factory()
    engine = FeeEngine(
        session_factory=factory,
        internal_transfer_rate=Decimal("0.01"),
        diaspora_rate=Decimal("0.02"),
        certified_statement_rate=Decimal("0.01"),
        tontine_rate=Decimal("0.01"),
    )

    with factory() as session:
        with session.begin():
            internal = engine.calculate_internal_transfer_fee(
                Decimal("100.00"),
                session=session,
                actor_id="actor-1",
                correlation_id="corr-1",
                transaction_id="tx-1",
            )
            diaspora = engine.calculate_diaspora_fee(
                Decimal("200.00"),
                session=session,
                actor_id="actor-1",
                correlation_id="corr-2",
                transaction_id="tx-2",
            )
            statement = engine.calculate_certified_statement_fee(
                Decimal("1500.00"),
                session=session,
                actor_id="actor-1",
                correlation_id="corr-3",
                transaction_id="tx-3",
            )
            tontine = engine.calculate_tontine_fee(
                Decimal("3300.00"),
                session=session,
                actor_id="actor-1",
                correlation_id="corr-4",
                transaction_id="tx-4",
            )

    assert internal.fee_amount == Decimal("1.00")
    assert diaspora.fee_amount == Decimal("4.00")
    assert statement.fee_amount == Decimal("15.00")
    assert tontine.fee_amount == Decimal("33.00")

    with factory() as session:
        audit_rows = list(session.execute(select(AuditChainEventModel)).scalars().all())

    assert len(audit_rows) == 4
    assert all(row.action == "BFOS_FEE_CALCULATED" for row in audit_rows)


def test_internal_transfer_fee_remains_one_percent() -> None:
    factory = _session_factory()
    engine = FeeEngine(
        session_factory=factory,
        internal_transfer_rate=Decimal("0.01"),
        diaspora_rate=Decimal("0.02"),
        certified_statement_rate=Decimal("0.01"),
        tontine_rate=Decimal("0.01"),
    )

    with factory() as session:
        with session.begin():
            internal = engine.calculate_internal_transfer_fee(
                Decimal("1000.00"),
                session=session,
                actor_id="actor-transfer",
                correlation_id="corr-transfer",
                transaction_id="tx-transfer",
            )

    assert internal.fee_amount == Decimal("10.00")
    assert internal.fee_amount != Decimal("30.00")
