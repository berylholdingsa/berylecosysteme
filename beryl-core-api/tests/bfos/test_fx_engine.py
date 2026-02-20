from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.fx_engine import FxEngine
from src.bfos.revenue_engine import RevenueEngine
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.fx_rates import FxRateModel, FxTransactionModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.revenue import RevenueRecordModel
from src.db.sqlalchemy import Base
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier


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


def test_fx_rate_integrity_and_transaction_recording() -> None:
    factory = _session_factory()
    revenue = RevenueEngine(session_factory=factory)
    engine = FxEngine(session_factory=factory, linked_revenue_engine=revenue)

    current_rate = engine.get_current_rate()
    assert current_rate > 0
    assert engine.validate_rate_integrity()

    first = engine.record_fx_transaction(
        Decimal("100.00"),
        transaction_id="fx-100",
        fee_payer="sender",
        actor_id="actor-fx",
        correlation_id="corr-fx-1",
    )
    second = engine.record_fx_transaction(
        Decimal("100.00"),
        transaction_id="fx-100",
        fee_payer="sender",
        actor_id="actor-fx",
        correlation_id="corr-fx-1",
    )

    assert first["idempotent"] is False
    assert second["idempotent"] is True

    with factory() as session:
        fx_rows = list(session.execute(select(FxTransactionModel)).scalars().all())
        revenue_rows = list(session.execute(select(RevenueRecordModel)).scalars().all())

    assert len(fx_rows) == 1
    assert len(revenue_rows) == 2

    fx_row = fx_rows[0]
    signed_payload = dict(fx_row.payload)
    signed_payload["signature"] = fx_row.signature
    assert event_signature_verifier.verify(signed_payload)

    expected_hash = hashlib.sha256(
        json.dumps(fx_row.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assert fx_row.payload_hash == expected_hash
