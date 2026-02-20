"""GreenOS asymmetric Ed25519 signatures for ledger and MRV exports.

Revision ID: 20260217_0006
Revises: 20260217_0005
Create Date: 2026-02-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260217_0006"
down_revision = "20260217_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("esg_impact_ledger", sa.Column("asym_signature", sa.Text(), nullable=True))
    op.add_column("esg_impact_ledger", sa.Column("asym_algorithm", sa.String(length=32), nullable=True))
    op.add_column("esg_impact_ledger", sa.Column("asym_key_version", sa.String(length=32), nullable=True))

    op.add_column("esg_mrv_exports", sa.Column("asym_signature", sa.Text(), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("asym_algorithm", sa.String(length=32), nullable=True))
    op.add_column("esg_mrv_exports", sa.Column("asym_key_version", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("esg_mrv_exports", "asym_key_version")
    op.drop_column("esg_mrv_exports", "asym_algorithm")
    op.drop_column("esg_mrv_exports", "asym_signature")

    op.drop_column("esg_impact_ledger", "asym_key_version")
    op.drop_column("esg_impact_ledger", "asym_algorithm")
    op.drop_column("esg_impact_ledger", "asym_signature")
