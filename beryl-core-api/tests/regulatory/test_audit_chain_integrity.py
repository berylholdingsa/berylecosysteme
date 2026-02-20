from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.core.audit.service import AuditService


@dataclass
class FakeAuditRow:
    actor_id: str
    action: str
    amount: Decimal
    currency: str
    correlation_id: str
    previous_hash: str
    current_hash: str
    signature: str
    payload: dict


def test_audit_hash_and_signature_verification() -> None:
    service = AuditService()
    current_hash = service._compute_current_hash(  # pylint: disable=protected-access
        actor_id="actor-1",
        action="PAYMENT_CREATE",
        amount=Decimal("100.00"),
        currency="XOF",
        correlation_id="corr-1",
        previous_hash="GENESIS",
        payload={"k": "v"},
    )
    signature = service._sign_current_hash(current_hash)  # pylint: disable=protected-access

    row = FakeAuditRow(
        actor_id="actor-1",
        action="PAYMENT_CREATE",
        amount=Decimal("100.00"),
        currency="XOF",
        correlation_id="corr-1",
        previous_hash="GENESIS",
        current_hash=current_hash,
        signature=signature,
        payload={"k": "v"},
    )
    assert service._verify_row(row)  # pylint: disable=protected-access
