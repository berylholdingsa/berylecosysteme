"""Revenue tracking model for BFOS monetization."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.sqlalchemy import Base


class RevenueRecordModel(Base):
    __tablename__ = "revenue_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    debit_entry_id: Mapped[str] = mapped_column(String(64), nullable=False)
    credit_entry_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
