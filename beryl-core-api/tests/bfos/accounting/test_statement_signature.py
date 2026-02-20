from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import create_engine
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


def test_statement_signer_sign_and_verify() -> None:
    signer = _signer()
    payload_hash = hashlib.sha256(b"statement").hexdigest()
    signature = signer.sign_document(payload_hash)

    assert signer.verify_signature(payload_hash, signature)
    assert not signer.verify_signature(payload_hash + "00", signature)


def test_statement_verification_detects_hash_mismatch() -> None:
    factory = _session_factory()
    signer = _signer()
    engine = StatementEngine(
        session_factory=factory,
        accounting=MerchantAccountingEngine(session_factory=factory),
        fees=FeeEngine(session_factory=factory),
        revenues=RevenueEngine(session_factory=factory),
        signer=signer,
    )

    now = datetime.now(timezone.utc)
    with factory() as session:
        with session.begin():
            session.add(
                FintechTransactionModel(
                    id=uuid.uuid4(),
                    actor_id="merchant-3",
                    amount=Decimal("900.00"),
                    currency="XOF",
                    target_account="wallet-sales",
                    status="ACCEPTED",
                    risk_score=Decimal("0"),
                    aml_flagged=False,
                    correlation_id="corr-stmt-2",
                    created_at=now - timedelta(days=8),
                )
            )

    result = engine.generate_statement("merchant-3", "3m", idempotency_key="stmt-idem-2")

    with factory() as session:
        with session.begin():
            row = session.query(CertifiedStatementModel).filter_by(statement_id=result["statement_id"]).one()
            row.pdf_blob = b"tampered-pdf"

    verification = engine.verify_statement(result["statement_id"])
    assert verification["valid"] is False
    assert verification["hash_ok"] is False
