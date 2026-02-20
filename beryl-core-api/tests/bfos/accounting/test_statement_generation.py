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


def test_statement_generation_persists_signed_immutable_statement() -> None:
    factory = _session_factory()
    accounting = MerchantAccountingEngine(session_factory=factory)
    fees = FeeEngine(session_factory=factory)
    revenues = RevenueEngine(session_factory=factory)
    signer = _signer()
    statements = StatementEngine(
        session_factory=factory,
        accounting=accounting,
        fees=fees,
        revenues=revenues,
        signer=signer,
    )

    now = datetime.now(timezone.utc)
    with factory() as session:
        with session.begin():
            session.add(
                FintechTransactionModel(
                    id=uuid.uuid4(),
                    actor_id="merchant-2",
                    amount=Decimal("1200.00"),
                    currency="XOF",
                    target_account="wallet-sales",
                    status="ACCEPTED",
                    risk_score=Decimal("0"),
                    aml_flagged=False,
                    correlation_id="corr-stmt-1",
                    created_at=now - timedelta(days=10),
                )
            )

    generated = statements.generate_statement(
        "merchant-2",
        "3m",
        idempotency_key="stmt-idem-1",
        merchant_name="Merchant 2",
    )

    assert generated["statement_id"].startswith("stmt-")
    assert len(generated["pdf_hash"]) == 64
    assert generated["signature"]
    assert generated["immutable"] is True

    verification = statements.verify_statement(generated["statement_id"])
    assert verification["valid"] is True

    with factory() as session:
        statement_rows = list(session.execute(select(CertifiedStatementModel)).scalars().all())
        signature_rows = list(session.execute(select(StatementSignatureModel)).scalars().all())

    assert len(statement_rows) == 1
    assert len(signature_rows) == 1
