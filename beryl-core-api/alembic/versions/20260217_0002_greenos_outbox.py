"""GreenOS transactional outbox table.

Revision ID: 20260217_0002
Revises: 20260213_0001
Create Date: 2026-02-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260217_0002"
down_revision = "20260213_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "esg_outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "event_type",
            name="uq_esg_outbox_aggregate_event",
        ),
    )
    op.create_index("ix_esg_outbox_events_status", "esg_outbox_events", ["status"])
    op.create_index("ix_esg_outbox_events_created_at", "esg_outbox_events", ["created_at"])
    op.create_index("ix_esg_outbox_events_aggregate_type", "esg_outbox_events", ["aggregate_type"])
    op.create_index("ix_esg_outbox_events_aggregate_id", "esg_outbox_events", ["aggregate_id"])
    op.create_index("ix_esg_outbox_events_event_type", "esg_outbox_events", ["event_type"])
    op.create_check_constraint(
        "chk_esg_outbox_status",
        "esg_outbox_events",
        "status IN ('PENDING','SENT','FAILED')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_esg_outbox_status", "esg_outbox_events", type_="check")
    op.drop_index("ix_esg_outbox_events_event_type", table_name="esg_outbox_events")
    op.drop_index("ix_esg_outbox_events_aggregate_id", table_name="esg_outbox_events")
    op.drop_index("ix_esg_outbox_events_aggregate_type", table_name="esg_outbox_events")
    op.drop_index("ix_esg_outbox_events_created_at", table_name="esg_outbox_events")
    op.drop_index("ix_esg_outbox_events_status", table_name="esg_outbox_events")
    op.drop_table("esg_outbox_events")
