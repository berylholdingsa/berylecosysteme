CREATE TABLE IF NOT EXISTS esg_impact_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  vehicle_id TEXT NOT NULL,
  country_code TEXT NOT NULL,
  geo_hash TEXT NOT NULL,
  distance_km NUMERIC(18,6) NOT NULL,
  co2_avoided_kg NUMERIC(18,6) NOT NULL,
  thermal_factor_local NUMERIC(18,8) NOT NULL,
  ev_factor_local NUMERIC(18,8) NOT NULL,
  model_version TEXT NOT NULL,
  event_hash TEXT NOT NULL,
  checksum TEXT NOT NULL,
  signature TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  event_timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_esg_impact_trip_model UNIQUE (trip_id, model_version),
  CONSTRAINT chk_esg_country_code_len CHECK (char_length(country_code) = 2)
);

CREATE INDEX IF NOT EXISTS idx_esg_impact_ledger_trip
  ON esg_impact_ledger(trip_id);

CREATE INDEX IF NOT EXISTS idx_esg_impact_ledger_country
  ON esg_impact_ledger(country_code);

CREATE INDEX IF NOT EXISTS idx_esg_impact_ledger_created_at
  ON esg_impact_ledger(created_at);

CREATE TABLE IF NOT EXISTS esg_audit_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  window_label TEXT NOT NULL,
  window_start TIMESTAMPTZ NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,
  country_code TEXT,
  methodology_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  report_hash TEXT NOT NULL UNIQUE,
  trips_count INTEGER NOT NULL,
  total_distance_km NUMERIC(18,6) NOT NULL,
  total_co2_avoided_kg NUMERIC(18,6) NOT NULL,
  correlation_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_esg_audit_metadata_created_at
  ON esg_audit_metadata(created_at);

CREATE INDEX IF NOT EXISTS idx_esg_audit_metadata_window
  ON esg_audit_metadata(window_start, window_end);

CREATE OR REPLACE FUNCTION prevent_esg_impact_ledger_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'esg_impact_ledger is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_esg_impact_ledger_no_update ON esg_impact_ledger;
CREATE TRIGGER trg_esg_impact_ledger_no_update
BEFORE UPDATE ON esg_impact_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_esg_impact_ledger_mutation();

DROP TRIGGER IF EXISTS trg_esg_impact_ledger_no_delete ON esg_impact_ledger;
CREATE TRIGGER trg_esg_impact_ledger_no_delete
BEFORE DELETE ON esg_impact_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_esg_impact_ledger_mutation();

CREATE OR REPLACE FUNCTION prevent_esg_audit_metadata_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'esg_audit_metadata is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_esg_audit_metadata_no_update ON esg_audit_metadata;
CREATE TRIGGER trg_esg_audit_metadata_no_update
BEFORE UPDATE ON esg_audit_metadata
FOR EACH ROW EXECUTE FUNCTION prevent_esg_audit_metadata_mutation();

DROP TRIGGER IF EXISTS trg_esg_audit_metadata_no_delete ON esg_audit_metadata;
CREATE TRIGGER trg_esg_audit_metadata_no_delete
BEFORE DELETE ON esg_audit_metadata
FOR EACH ROW EXECUTE FUNCTION prevent_esg_audit_metadata_mutation();
