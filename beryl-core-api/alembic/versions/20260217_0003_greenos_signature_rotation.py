"""GreenOS signature hardening for ledger and audit.

Revision ID: 20260217_0003
Revises: 20260217_0002
Create Date: 2026-02-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260217_0003"
down_revision = "20260217_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "esg_impact_ledger",
        sa.Column("signature_algorithm", sa.String(length=32), nullable=False, server_default="HMAC-SHA256"),
    )
    op.add_column(
        "esg_impact_ledger",
        sa.Column("key_version", sa.String(length=32), nullable=False, server_default="v1"),
    )

    op.add_column("esg_audit_metadata", sa.Column("signature", sa.Text(), nullable=True))
    op.add_column("esg_audit_metadata", sa.Column("signature_algorithm", sa.String(length=32), nullable=True))
    op.add_column("esg_audit_metadata", sa.Column("key_version", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("esg_audit_metadata", "key_version")
    op.drop_column("esg_audit_metadata", "signature_algorithm")
    op.drop_column("esg_audit_metadata", "signature")

    op.drop_column("esg_impact_ledger", "key_version")
    op.drop_column("esg_impact_ledger", "signature_algorithm")

