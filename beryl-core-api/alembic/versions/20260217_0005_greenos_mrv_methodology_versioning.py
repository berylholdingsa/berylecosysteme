"""GreenOS MRV methodology versioning and export linkage.

Revision ID: 20260217_0005
Revises: 20260217_0004
Create Date: 2026-02-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260217_0005"
down_revision = "20260217_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "esg_mrv_methodology",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("methodology_version", sa.String(length=64), nullable=False),
        sa.Column("baseline_description", sa.Text(), nullable=False),
        sa.Column("emission_factor_source", sa.String(length=255), nullable=False),
        sa.Column("thermal_factor_reference", sa.String(length=255), nullable=False),
        sa.Column("ev_factor_reference", sa.String(length=255), nullable=False),
        sa.Column("calculation_formula", sa.Text(), nullable=False),
        sa.Column("geographic_scope", sa.String(length=255), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.UniqueConstraint("methodology_version", name="uq_esg_mrv_methodology_version"),
    )
    op.create_index("ix_esg_mrv_methodology_created_at", "esg_mrv_methodology", ["created_at"])
    op.create_index("ix_esg_mrv_methodology_status", "esg_mrv_methodology", ["status"])
    op.create_check_constraint(
        "chk_esg_mrv_methodology_status",
        "esg_mrv_methodology",
        "status IN ('ACTIVE','DEPRECATED')",
    )
    op.create_index(
        "uq_esg_mrv_methodology_single_active",
        "esg_mrv_methodology",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    op.add_column("esg_mrv_exports", sa.Column("methodology_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("methodology_hash", sa.Text(), nullable=True))
    op.create_index("ix_esg_mrv_exports_methodology_id", "esg_mrv_exports", ["methodology_id"])
    op.create_foreign_key(
        "fk_esg_mrv_exports_methodology_id",
        "esg_mrv_exports",
        "esg_mrv_methodology",
        ["methodology_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_esg_mrv_exports_methodology_id", "esg_mrv_exports", type_="foreignkey")
    op.drop_index("ix_esg_mrv_exports_methodology_id", table_name="esg_mrv_exports")
    op.drop_column("esg_mrv_exports", "methodology_hash")
    op.drop_column("esg_mrv_exports", "methodology_id")

    op.drop_index("uq_esg_mrv_methodology_single_active", table_name="esg_mrv_methodology")
    op.drop_constraint("chk_esg_mrv_methodology_status", "esg_mrv_methodology", type_="check")
    op.drop_index("ix_esg_mrv_methodology_status", table_name="esg_mrv_methodology")
    op.drop_index("ix_esg_mrv_methodology_created_at", table_name="esg_mrv_methodology")
    op.drop_table("esg_mrv_methodology")

