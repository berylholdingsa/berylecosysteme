"""GreenOS MRV exports materialized table.

Revision ID: 20260217_0004
Revises: 20260217_0003
Create Date: 2026-02-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260217_0004"
down_revision = "20260217_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "esg_mrv_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_co2_avoided", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("total_distance", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("methodology_version", sa.String(length=128), nullable=False),
        sa.Column("baseline_reference", sa.String(length=255), nullable=False),
        sa.Column("emission_factor_source", sa.String(length=255), nullable=False),
        sa.Column("verification_hash", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("signature_algorithm", sa.String(length=32), nullable=False, server_default="HMAC-SHA256"),
        sa.Column("key_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("period_start", "period_end", name="uq_esg_mrv_export_period"),
    )
    op.create_index("ix_esg_mrv_export_status", "esg_mrv_exports", ["status"])
    op.create_index("ix_esg_mrv_export_created_at", "esg_mrv_exports", ["created_at"])
    op.create_check_constraint(
        "chk_esg_mrv_export_status",
        "esg_mrv_exports",
        "status IN ('DRAFT','VERIFIED','EXPORTED')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_esg_mrv_export_status", "esg_mrv_exports", type_="check")
    op.drop_index("ix_esg_mrv_export_created_at", table_name="esg_mrv_exports")
    op.drop_index("ix_esg_mrv_export_status", table_name="esg_mrv_exports")
    op.drop_table("esg_mrv_exports")

