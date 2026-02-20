"""Certified statement persistence models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, LargeBinary, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.sqlalchemy import Base


class CertifiedStatementModel(Base):
    __tablename__ = "certified_statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    merchant_name: Mapped[str] = mapped_column(String(256), nullable=False)
    period_label: Mapped[str] = mapped_column(String(16), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_sales: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_result: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cashflow: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    statement_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    pdf_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    embedded_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    signature_key_id: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_url: Mapped[str] = mapped_column(String(512), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    revenue_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StatementSignatureModel(Base):
    __tablename__ = "statement_signatures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_ref: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("certified_statements.id"),
        nullable=False,
        index=True,
    )
    signed_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    public_key_pem: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
