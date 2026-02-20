from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.revenue_engine import RevenueEngine
from src.db.models.audit_chain import AuditChainEventModel
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
        ],
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_record_revenue_is_idempotent_and_ledgered() -> None:
    factory = _session_factory()
    engine = RevenueEngine(session_factory=factory)

    first = engine.record_revenue(
        source="internal_transfer_fee",
        amount=Decimal("12.50"),
        currency="XOF",
        transaction_id="tx-rev-1",
        actor_id="fintech-user-1",
        correlation_id="corr-rev-1",
    )
    second = engine.record_revenue(
        source="internal_transfer_fee",
        amount=Decimal("12.50"),
        currency="XOF",
        transaction_id="tx-rev-1",
        actor_id="fintech-user-1",
        correlation_id="corr-rev-1",
    )

    assert first["idempotent"] is False
    assert second["idempotent"] is True

    with factory() as session:
        revenue_rows = list(session.execute(select(RevenueRecordModel)).scalars().all())
        ledger_rows = list(session.execute(select(LedgerEntryModel)).scalars().all())
        audit_rows = list(session.execute(select(AuditChainEventModel)).scalars().all())

    assert len(revenue_rows) == 1
    assert len(ledger_rows) == 2
    assert len(audit_rows) >= 1

    row = revenue_rows[0]
    signed_payload = dict(row.payload)
    signed_payload["signature"] = row.signature
    assert event_signature_verifier.verify(signed_payload)

    expected_hash = hashlib.sha256(
        json.dumps(row.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assert row.payload_hash == expected_hash


def test_revenue_summary_aggregates_period() -> None:
    factory = _session_factory()
    engine = RevenueEngine(session_factory=factory)

    engine.record_revenue("internal_transfer_fee", Decimal("10.00"), "XOF", "tx-a", actor_id="a", correlation_id="c1")
    engine.record_revenue("diaspora_fee", Decimal("20.00"), "XOF", "tx-b", actor_id="a", correlation_id="c2")

    summary = engine.get_revenue_summary("30d")
    assert summary["period"] == "30d"
    assert Decimal(summary["total_amount"]) == Decimal("30.00")
    assert len(summary["items"]) == 2
