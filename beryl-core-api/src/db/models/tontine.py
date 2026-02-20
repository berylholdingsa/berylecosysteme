"""Tontine persistence models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.sqlalchemy import Base


class TontineGroupModel(Base):
    __tablename__ = "tontine_groups"
    __table_args__ = (
        CheckConstraint("max_members >= 2 AND max_members <= 10", name="ck_tontine_max_members_2_10"),
        CheckConstraint(
            "frequency_type IN ('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY')",
            name="ck_tontine_frequency_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_group_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    contribution_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    frequency_type: Mapped[str] = mapped_column(String(16), nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    security_code_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    signature_hash: Mapped[str] = mapped_column(String(128), nullable=False)


class TontineMemberModel(Base):
    __tablename__ = "tontine_members"
    __table_args__ = (
        UniqueConstraint("tontine_id", "user_id", name="uq_tontine_member"),
        CheckConstraint("reputation_score >= 0 AND reputation_score <= 100", name="ck_tontine_reputation_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tontine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tontine_groups.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    reputation_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("50.00"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TontineCycleModel(Base):
    __tablename__ = "tontine_cycles"
    __table_args__ = (
        UniqueConstraint("tontine_id", "cycle_number", name="uq_tontine_cycle_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tontine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tontine_groups.id"), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    total_pool: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    next_distribution_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    commission_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))


class TontineWithdrawRequestModel(Base):
    __tablename__ = "tontine_withdraw_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tontine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tontine_groups.id"), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TontineVoteModel(Base):
    __tablename__ = "tontine_votes"
    __table_args__ = (
        UniqueConstraint("withdraw_request_id", "user_id", name="uq_tontine_vote_unique"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tontine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tontine_groups.id"), nullable=False, index=True)
    withdraw_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tontine_withdraw_requests.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
