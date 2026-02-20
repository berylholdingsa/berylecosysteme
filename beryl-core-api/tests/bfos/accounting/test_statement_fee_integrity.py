from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.accounting.merchant_accounting_engine import MerchantAccountingEngine
from src.bfos.accounting.statement_engine import StatementEngine
from src.bfos.accounting.statement_signer import StatementSigner
from src.bfos.fee_engine import FeeEngine
from src.bfos.revenue_engine import RevenueEngine
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.fintech import FintechTransactionModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.revenue import RevenueRecordModel
from src.db.models.statements import CertifiedStatementModel, StatementSignatureModel
from src.db.sqlalchemy import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AuditChainEventModel.__table__,
            FintechTransactionModel.__table__,
            IdempotencyKeyModel.__table__,
            LedgerUserModel.__table__,
            LedgerAccountModel.__table__,
            LedgerEntryModel.__table__,
            RevenueRecordModel.__table__,
            CertifiedStatementModel.__table__,
            StatementSignatureModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def _signer() -> StatementSigner:
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return StatementSigner(private_key_pem=pem)


def test_statement_fee_is_charged_only_during_generation_and_ledgered() -> None:
    factory = _session_factory()
    engine = StatementEngine(
        session_factory=factory,
        accounting=MerchantAccountingEngine(session_factory=factory),
        fees=FeeEngine(session_factory=factory),
        revenues=RevenueEngine(session_factory=factory),
        signer=_signer(),
    )

    now = datetime.now(timezone.utc)
    with factory() as session:
        with session.begin():
            session.add(
                FintechTransactionModel(
                    id=uuid.uuid4(),
                    actor_id="merchant-4",
                    amount=Decimal("2000.00"),
                    currency="XOF",
                    target_account="wallet-sales",
                    status="ACCEPTED",
                    risk_score=Decimal("0"),
                    aml_flagged=False,
                    correlation_id="corr-stmt-3",
                    created_at=now - timedelta(days=20),
                )
            )

    with factory() as session:
        before = list(session.execute(select(RevenueRecordModel)).scalars().all())
    assert len(before) == 0

    first = engine.generate_statement("merchant-4", "6m", idempotency_key="stmt-idem-3")
    second = engine.generate_statement("merchant-4", "6m", idempotency_key="stmt-idem-3")

    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert Decimal(first["statement_fee"]) == Decimal("20.00")

    with factory() as session:
        revenue_rows = list(
            session.execute(
                select(RevenueRecordModel).where(RevenueRecordModel.source == "certified_statement_fee")
            ).scalars().all()
        )
        ledger_rows = list(
            session.execute(
                select(LedgerEntryModel).where(LedgerEntryModel.reference.like("statement-fee:%"))
            ).scalars().all()
        )
        audit_rows = list(
            session.execute(
                select(AuditChainEventModel).where(AuditChainEventModel.action == "BFOS_CERTIFIED_STATEMENT_GENERATED")
            ).scalars().all()
        )

    assert len(revenue_rows) == 1
    assert Decimal(str(revenue_rows[0].amount)) == Decimal("20.00")
    assert len(ledger_rows) == 2
    assert {entry.direction for entry in ledger_rows} == {"DEBIT", "CREDIT"}
    assert len(audit_rows) == 1
