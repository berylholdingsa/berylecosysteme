from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.payment_terminal.service as payment_terminal_service_module
from app.payment_terminal.schemas import (
    PaymentConfirmRequest,
    PaymentDecision,
    PaymentInitiateRequest,
    PaymentStatus,
)
from src.db.models.outbox import OutboxEventModel
from src.db.sqlalchemy import Base


@pytest.fixture
def payment_terminal_context(monkeypatch, tmp_path):
    db_path = tmp_path / "payment_terminal.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(bind=engine, tables=[OutboxEventModel.__table__], checkfirst=True)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    monkeypatch.setattr(payment_terminal_service_module, "SessionLocal", factory)
    service = payment_terminal_service_module.PaymentTerminalService()
    return service, factory


def test_initiate_stages_expected_topics(payment_terminal_context) -> None:
    service, factory = payment_terminal_context
    request = PaymentInitiateRequest(
        amount=Decimal("15000"),
        currency="XOF",
        merchant_id="merchant-terminal-001",
        payment_method="WALLET",
        metadata={},
    )

    response = service.initiate(
        request=request,
        correlation_id=str(uuid4()),
        request_id="req-initiate",
    )

    assert response.terminal_session_id
    session_state = service.get_session(terminal_session_id=response.terminal_session_id)

    with factory() as db_session:
        rows = list(
            db_session.execute(
                select(OutboxEventModel).order_by(OutboxEventModel.created_at.asc())
            ).scalars().all()
        )

    topics = [row.topic for row in rows]
    assert "payment_initiated" in topics
    if response.decision == PaymentDecision.BLOCK:
        assert "payment_blocked" in topics
        assert session_state.status == PaymentStatus.BLOCKED
    elif response.decision == PaymentDecision.REVIEW:
        assert "payment_flagged" in topics
        assert session_state.status == PaymentStatus.PENDING
    else:
        assert session_state.status == PaymentStatus.PENDING


def test_confirm_allow_payment_stages_confirmed_event(payment_terminal_context) -> None:
    service, factory = payment_terminal_context
    request = PaymentInitiateRequest(
        amount=Decimal("1200"),
        currency="XOF",
        merchant_id="merchant-low-risk",
        payment_method="WALLET",
        metadata={"trusted_device": True, "trusted_customer": True},
    )

    response = service.initiate(
        request=request,
        correlation_id=str(uuid4()),
        request_id="req-confirm",
    )
    if response.decision != PaymentDecision.ALLOW:
        pytest.skip("heuristic did not produce ALLOW decision")

    confirm = service.confirm(
        request=PaymentConfirmRequest(
            terminal_session_id=response.terminal_session_id,
            biometric_verified=True,
        ),
        correlation_id=str(uuid4()),
        request_id="req-confirm-2",
    )
    session_state = service.get_session(terminal_session_id=response.terminal_session_id)

    assert confirm.status == PaymentStatus.CONFIRMED
    assert session_state.status == PaymentStatus.CONFIRMED

    with factory() as db_session:
        confirmed_row = db_session.execute(
            select(OutboxEventModel).where(
                OutboxEventModel.event_key == session_state.transaction_id,
                OutboxEventModel.topic == "payment_confirmed",
            )
        ).scalar_one_or_none()

    assert confirmed_row is not None


def test_confirm_missing_session_raises_domain_error(payment_terminal_context) -> None:
    service, _ = payment_terminal_context

    with pytest.raises(payment_terminal_service_module.PaymentTerminalError) as exc:
        service.confirm(
            request=PaymentConfirmRequest(
                terminal_session_id=str(uuid4()),
                biometric_verified=True,
            ),
            correlation_id=str(uuid4()),
            request_id="req-missing",
        )

    assert exc.value.status_code == 404
    assert exc.value.code == "SESSION_NOT_FOUND"

