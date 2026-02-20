CREATE TABLE IF NOT EXISTS revenue_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL,
  amount NUMERIC(18,2) NOT NULL,
  currency TEXT NOT NULL,
  transaction_id TEXT NOT NULL UNIQUE,
  idempotency_key TEXT NOT NULL UNIQUE,
  payload_hash TEXT NOT NULL,
  signature TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  debit_entry_id TEXT NOT NULL,
  credit_entry_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_revenue_source_created_at ON revenue_records(source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_correlation ON revenue_records(correlation_id);
