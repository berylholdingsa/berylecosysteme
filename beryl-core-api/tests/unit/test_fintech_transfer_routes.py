from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

import src.api.v1.routes.fintech_routes as fintech_routes
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.compliance import SuspiciousActivityLogModel
from src.db.models.fintech import FintechTransactionModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.revenue import RevenueRecordModel
from src.db.sqlalchemy import Base


def _request(path: str) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "query_string": b"",
        "headers": [(b"x-correlation-id", str(uuid4()).encode("utf-8"))],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


@pytest.fixture
def fintech_transfer_db(monkeypatch, tmp_path):
    db_path = tmp_path / "fintech_transfer.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AuditChainEventModel.__table__,
            IdempotencyKeyModel.__table__,
            SuspiciousActivityLogModel.__table__,
            FintechTransactionModel.__table__,
            RevenueRecordModel.__table__,
            LedgerUserModel.__table__,
            LedgerAccountModel.__table__,
            LedgerEntryModel.__table__,
        ],
    )
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    monkeypatch.setattr(fintech_routes, "SessionLocal", factory)
    return factory


def test_transfer_preview_uses_backend_fee_1_percent(fintech_transfer_db) -> None:
    _ = fintech_transfer_db
    payload = fintech_routes.TransferPreviewRequest(
        actor_id="fintech_123",
        amount=Decimal("100000.00"),
        currency="XOF",
        destination_country="CI",
    )

    response = fintech_routes.preview_transfer(
        request=payload,
        http_request=_request("/api/v1/fintech/transfer/preview"),
    )

    assert Decimal(response.gross_amount) == Decimal("100000.00")
    assert Decimal(response.fee_amount) == Decimal("1000.00")
    assert Decimal(response.net_amount) == Decimal("99000.00")
    assert Decimal(response.fee_amount) != Decimal("3000.00")


def test_transfer_executes_double_entry_and_returns_amounts(fintech_transfer_db) -> None:
    payload = fintech_routes.TransferExecuteRequest(
        actor_id="fintech_123",
        amount=Decimal("50000.00"),
        currency="XOF",
        destination_country="SN",
        target_account="recipient-001",
        reference="inv-2026-02",
    )

    response = fintech_routes.execute_transfer(
        request=payload,
        http_request=_request("/api/v1/fintech/transfer"),
        idempotency_key=str(uuid4()),
    )

    assert response.transaction_id
    assert response.currency == "XOF"
    assert Decimal(response.gross_amount) == Decimal("50000.00")
    assert Decimal(response.fee_amount) == Decimal("500.00")
    assert Decimal(response.net_amount) == Decimal("49500.00")
    assert Decimal(response.fee_amount) != Decimal("1500.00")

    with fintech_transfer_db() as session:
        ledger_rows = list(
            session.execute(
                select(LedgerEntryModel).where(LedgerEntryModel.reference == response.transaction_id)
            ).scalars().all()
        )
        revenue_row = session.execute(
            select(RevenueRecordModel).where(RevenueRecordModel.transaction_id == f"{response.transaction_id}:fee")
        ).scalar_one_or_none()
        transfer_audit = session.execute(
            select(AuditChainEventModel).where(AuditChainEventModel.action == "TRANSFER_EXECUTED")
        ).scalar_one_or_none()

    assert len(ledger_rows) == 2
    assert {row.direction for row in ledger_rows} == {"DEBIT", "CREDIT"}
    assert all(Decimal(str(row.amount)) == Decimal("49500.00") for row in ledger_rows)
    assert revenue_row is not None
    assert Decimal(str(revenue_row.amount)) == Decimal("500.00")
    assert transfer_audit is not None


def test_transfer_rejects_duplicate_idempotency_key(fintech_transfer_db) -> None:
    _ = fintech_transfer_db
    idem_key = str(uuid4())
    payload = fintech_routes.TransferExecuteRequest(
        actor_id="fintech_123",
        amount=Decimal("1000.00"),
        currency="XOF",
        destination_country="SN",
        target_account="recipient-001",
    )

    first = fintech_routes.execute_transfer(
        request=payload,
        http_request=_request("/api/v1/fintech/transfer"),
        idempotency_key=idem_key,
    )

    assert first.transaction_id

    with pytest.raises(HTTPException) as exc:
        fintech_routes.execute_transfer(
            request=payload,
            http_request=_request("/api/v1/fintech/transfer"),
            idempotency_key=idem_key,
        )
    assert exc.value.status_code == 409
    assert exc.value.detail == "Duplicate idempotency key"
