"""FX rates and FX transaction tracking models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.sqlalchemy import Base


class FxRateModel(Base):
    __tablename__ = "fx_rates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    rate_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="bfos-default")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FxTransactionModel(Base):
    __tablename__ = "fx_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    converted_amount_cfa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    applied_rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    fee_payer: Mapped[str] = mapped_column(String(16), nullable=False)
    fee_amount_cfa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    margin_amount_cfa: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
