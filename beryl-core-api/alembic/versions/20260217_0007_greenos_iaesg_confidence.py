"""GreenOS IAESG confidence and anomaly persistence.

Revision ID: 20260217_0007
Revises: 20260217_0006
Create Date: 2026-02-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260217_0007"
down_revision = "20260217_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("esg_impact_ledger", sa.Column("confidence_score", sa.Integer(), nullable=True))
    op.add_column("esg_impact_ledger", sa.Column("integrity_index", sa.Integer(), nullable=True))
    op.add_column("esg_impact_ledger", sa.Column("anomaly_flags", sa.JSON(), nullable=True))
    op.add_column("esg_impact_ledger", sa.Column("aoq_status", sa.String(length=16), nullable=True))
    op.add_column("esg_impact_ledger", sa.Column("explanation", sa.JSON(), nullable=True))

    op.add_column("esg_mrv_exports", sa.Column("confidence_score", sa.Integer(), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("integrity_index", sa.Integer(), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("anomaly_flags", sa.JSON(), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("aoq_status", sa.String(length=16), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("explanation", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("esg_mrv_exports", "explanation")
    op.drop_column("esg_mrv_exports", "aoq_status")
    op.drop_column("esg_mrv_exports", "anomaly_flags")
    op.drop_column("esg_mrv_exports", "integrity_index")
    op.drop_column("esg_mrv_exports", "confidence_score")

    op.drop_column("esg_impact_ledger", "explanation")
    op.drop_column("esg_impact_ledger", "aoq_status")
    op.drop_column("esg_impact_ledger", "anomaly_flags")
    op.drop_column("esg_impact_ledger", "integrity_index")
    op.drop_column("esg_impact_ledger", "confidence_score")
