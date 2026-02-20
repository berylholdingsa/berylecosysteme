"""GreenOS foundation migration (Lot 1).

Revision ID: 20260213_0001
Revises:
Create Date: 2026-02-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260213_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "esg_impact_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trip_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("vehicle_id", sa.String(length=128), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("geo_hash", sa.String(length=32), nullable=False),
        sa.Column("distance_km", sa.Numeric(18, 6), nullable=False),
        sa.Column("co2_avoided_kg", sa.Numeric(18, 6), nullable=False),
        sa.Column("thermal_factor_local", sa.Numeric(18, 8), nullable=False),
        sa.Column("ev_factor_local", sa.Numeric(18, 8), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("trip_id", "model_version", name="uq_esg_impact_trip_model"),
    )
    op.create_index("ix_esg_impact_ledger_created_at", "esg_impact_ledger", ["created_at"])
    op.create_index("ix_esg_impact_ledger_trip_id", "esg_impact_ledger", ["trip_id"])
    op.create_index("ix_esg_impact_ledger_country_code", "esg_impact_ledger", ["country_code"])
    op.create_check_constraint(
        "chk_esg_country_code_len",
        "esg_impact_ledger",
        "char_length(country_code) = 2",
    )

    op.create_table(
        "esg_audit_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("window_label", sa.String(length=8), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("methodology_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("report_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("trips_count", sa.Integer(), nullable=False),
        sa.Column("total_distance_km", sa.Numeric(18, 6), nullable=False),
        sa.Column("total_co2_avoided_kg", sa.Numeric(18, 6), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_esg_audit_metadata_created_at", "esg_audit_metadata", ["created_at"])
    op.create_index("ix_esg_audit_metadata_window", "esg_audit_metadata", ["window_start", "window_end"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_esg_impact_ledger_mutation()
        RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'esg_impact_ledger is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_esg_impact_ledger_no_update
        BEFORE UPDATE ON esg_impact_ledger
        FOR EACH ROW EXECUTE FUNCTION prevent_esg_impact_ledger_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_esg_impact_ledger_no_delete
        BEFORE DELETE ON esg_impact_ledger
        FOR EACH ROW EXECUTE FUNCTION prevent_esg_impact_ledger_mutation();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_esg_audit_metadata_mutation()
        RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'esg_audit_metadata is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_esg_audit_metadata_no_update
        BEFORE UPDATE ON esg_audit_metadata
        FOR EACH ROW EXECUTE FUNCTION prevent_esg_audit_metadata_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_esg_audit_metadata_no_delete
        BEFORE DELETE ON esg_audit_metadata
        FOR EACH ROW EXECUTE FUNCTION prevent_esg_audit_metadata_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_esg_audit_metadata_no_delete ON esg_audit_metadata")
    op.execute("DROP TRIGGER IF EXISTS trg_esg_audit_metadata_no_update ON esg_audit_metadata")
    op.execute("DROP FUNCTION IF EXISTS prevent_esg_audit_metadata_mutation()")
    op.execute("DROP TRIGGER IF EXISTS trg_esg_impact_ledger_no_delete ON esg_impact_ledger")
    op.execute("DROP TRIGGER IF EXISTS trg_esg_impact_ledger_no_update ON esg_impact_ledger")
    op.execute("DROP FUNCTION IF EXISTS prevent_esg_impact_ledger_mutation()")
    op.drop_index("ix_esg_audit_metadata_window", table_name="esg_audit_metadata")
    op.drop_index("ix_esg_audit_metadata_created_at", table_name="esg_audit_metadata")
    op.drop_table("esg_audit_metadata")
    op.drop_constraint("chk_esg_country_code_len", "esg_impact_ledger", type_="check")
    op.drop_index("ix_esg_impact_ledger_country_code", table_name="esg_impact_ledger")
    op.drop_index("ix_esg_impact_ledger_trip_id", table_name="esg_impact_ledger")
    op.drop_index("ix_esg_impact_ledger_created_at", table_name="esg_impact_ledger")
    op.drop_table("esg_impact_ledger")

