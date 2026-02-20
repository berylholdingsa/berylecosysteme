"""SQLAlchemy models for GreenOS ESG ledger and audit metadata."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, event
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.sqlalchemy import Base


class EsgImpactLedgerModel(Base):
    """Append-only ESG impact ledger (immutable once inserted)."""

    __tablename__ = "esg_impact_ledger"
    __table_args__ = (
        UniqueConstraint("trip_id", "model_version", name="uq_esg_impact_trip_model"),
        Index("ix_esg_impact_ledger_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    vehicle_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    geo_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    distance_km: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    co2_avoided_kg: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    thermal_factor_local: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    ev_factor_local: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_hash: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="HMAC-SHA256")
    key_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    asym_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    asym_algorithm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    asym_key_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    integrity_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_flags: Mapped[list[str] | None] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    aoq_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EsgAuditMetadataModel(Base):
    """Append-only metadata for GreenOS audit previews/reports."""

    __tablename__ = "esg_audit_metadata"
    __table_args__ = (
        Index("ix_esg_audit_metadata_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    window_label: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    methodology_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    report_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_algorithm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    key_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trips_count: Mapped[int] = mapped_column(nullable=False)
    total_distance_km: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_co2_avoided_kg: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EsgOutboxEventModel(Base):
    """Transactional outbox rows for reliable GreenOS Kafka delivery."""

    __tablename__ = "esg_outbox_events"
    __table_args__ = (
        UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "event_type",
            name="uq_esg_outbox_aggregate_event",
        ),
        CheckConstraint("status IN ('PENDING','SENT','FAILED')", name="chk_esg_outbox_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EsgMrvExportModel(Base):
    """Materialized MRV export snapshots for climate certification workflows."""

    __tablename__ = "esg_mrv_exports"
    __table_args__ = (
        UniqueConstraint("period_start", "period_end", name="uq_esg_mrv_export_period"),
        CheckConstraint("status IN ('DRAFT','VERIFIED','EXPORTED')", name="chk_esg_mrv_export_status"),
        Index("ix_esg_mrv_export_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    methodology_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("esg_mrv_methodology.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_co2_avoided: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_distance: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(128), nullable=False)
    methodology_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    emission_factor_source: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_hash: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="HMAC-SHA256")
    key_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    asym_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    asym_algorithm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    asym_key_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    integrity_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_flags: Mapped[list[str] | None] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    aoq_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EsgMrvMethodologyModel(Base):
    """Versioned MRV methodology registry for institutional traceability."""

    __tablename__ = "esg_mrv_methodology"
    __table_args__ = (
        UniqueConstraint("methodology_version", name="uq_esg_mrv_methodology_version"),
        CheckConstraint("status IN ('ACTIVE','DEPRECATED')", name="chk_esg_mrv_methodology_status"),
        Index("ix_esg_mrv_methodology_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    methodology_version: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_description: Mapped[str] = mapped_column(Text, nullable=False)
    emission_factor_source: Mapped[str] = mapped_column(String(255), nullable=False)
    thermal_factor_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    ev_factor_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    calculation_formula: Mapped[str] = mapped_column(Text, nullable=False)
    geographic_scope: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", index=True)


@event.listens_for(EsgImpactLedgerModel, "before_update", propagate=True)
def _prevent_impact_update(*args, **kwargs) -> None:
    raise ValueError("esg_impact_ledger is append-only and cannot be updated")


@event.listens_for(EsgImpactLedgerModel, "before_delete", propagate=True)
def _prevent_impact_delete(*args, **kwargs) -> None:
    raise ValueError("esg_impact_ledger is append-only and cannot be deleted")


@event.listens_for(EsgAuditMetadataModel, "before_update", propagate=True)
def _prevent_audit_update(*args, **kwargs) -> None:
    raise ValueError("esg_audit_metadata is append-only and cannot be updated")


@event.listens_for(EsgAuditMetadataModel, "before_delete", propagate=True)
def _prevent_audit_delete(*args, **kwargs) -> None:
    raise ValueError("esg_audit_metadata is append-only and cannot be deleted")
