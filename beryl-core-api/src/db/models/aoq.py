"""SQLAlchemy models for AOQ persistence."""

import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.sqlalchemy import Base


class AoqRuleModel(Base):
    __tablename__ = "aoq_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    weights: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def weight_fintech(self) -> float:
        return float(self.weights.get("fintech", 0.35))

    @property
    def weight_mobility(self) -> float:
        return float(self.weights.get("mobility", 0.25))

    @property
    def weight_esg(self) -> float:
        return float(self.weights.get("esg", 0.25))

    @property
    def weight_social(self) -> float:
        return float(self.weights.get("social", 0.15))

    @property
    def version(self) -> int:
        # Column does not exist in production schema; keep API compatibility.
        return int(self.weights.get("version", 1))


class AoqSignalModel(Base):
    __tablename__ = "aoq_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="mobile")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AoqDecisionModel(Base):
    __tablename__ = "aoq_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("aoq_signals.id"), nullable=False)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("aoq_rules.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AoqLedgerEntryModel(Base):
    __tablename__ = "aoq_ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("aoq_decisions.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    impact_type: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AoqAuditTrailModel(Base):
    __tablename__ = "aoq_audit_trail"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
    )
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
