CREATE TABLE IF NOT EXISTS audit_chain_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id TEXT NOT NULL UNIQUE,
  actor_id TEXT NOT NULL,
  action TEXT NOT NULL,
  amount NUMERIC(18,2),
  currency TEXT,
  correlation_id TEXT NOT NULL,
  previous_hash TEXT NOT NULL,
  current_hash TEXT NOT NULL,
  signature TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_chain_created_at ON audit_chain_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_chain_actor_id ON audit_chain_events(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_chain_correlation_id ON audit_chain_events(correlation_id);

CREATE OR REPLACE FUNCTION prevent_audit_chain_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_chain_events is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_audit_chain_update ON audit_chain_events;
CREATE TRIGGER trg_prevent_audit_chain_update
BEFORE UPDATE ON audit_chain_events
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_chain_mutation();

DROP TRIGGER IF EXISTS trg_prevent_audit_chain_delete ON audit_chain_events;
CREATE TRIGGER trg_prevent_audit_chain_delete
BEFORE DELETE ON audit_chain_events
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_chain_mutation();
