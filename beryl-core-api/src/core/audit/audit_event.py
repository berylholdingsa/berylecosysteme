"""Domain object for immutable audit trail records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    actor_id: str
    action: str
    amount: Decimal | None
    currency: str | None
    timestamp: datetime
    correlation_id: str
    previous_hash: str
    current_hash: str
    signature: str
    payload: dict

    @classmethod
    def build(
        cls,
        *,
        actor_id: str,
        action: str,
        amount: Decimal | None,
        currency: str | None,
        correlation_id: str,
        previous_hash: str,
        current_hash: str,
        signature: str,
        payload: dict,
    ) -> "AuditEvent":
        return cls(
            event_id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            amount=amount,
            currency=currency,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            signature=signature,
            payload=payload,
        )
