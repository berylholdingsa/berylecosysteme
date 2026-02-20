CREATE TABLE IF NOT EXISTS fintech_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id TEXT NOT NULL,
  amount NUMERIC(18,2) NOT NULL,
  currency TEXT NOT NULL,
  target_account TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ACCEPTED',
  risk_score NUMERIC(6,2) NOT NULL DEFAULT 0,
  aml_flagged BOOLEAN NOT NULL DEFAULT FALSE,
  correlation_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fintech_tx_actor ON fintech_transactions(actor_id);
CREATE INDEX IF NOT EXISTS idx_fintech_tx_correlation ON fintech_transactions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_fintech_tx_created_at ON fintech_transactions(created_at DESC);
