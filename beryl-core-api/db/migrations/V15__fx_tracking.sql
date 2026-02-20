CREATE TABLE IF NOT EXISTS fx_rates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_currency TEXT NOT NULL,
  quote_currency TEXT NOT NULL,
  rate NUMERIC(18,6) NOT NULL,
  rate_hash TEXT NOT NULL,
  signature TEXT NOT NULL,
  source TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fx_rates_pair_active ON fx_rates(base_currency, quote_currency, is_active, created_at DESC);

CREATE TABLE IF NOT EXISTS fx_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id TEXT NOT NULL UNIQUE,
  idempotency_key TEXT NOT NULL UNIQUE,
  actor_id TEXT NOT NULL,
  amount_usd NUMERIC(18,2) NOT NULL,
  converted_amount_cfa NUMERIC(18,2) NOT NULL,
  applied_rate NUMERIC(18,6) NOT NULL,
  fee_payer TEXT NOT NULL,
  fee_amount_cfa NUMERIC(18,2) NOT NULL,
  margin_amount_cfa NUMERIC(18,2) NOT NULL,
  payload_hash TEXT NOT NULL,
  signature TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fx_transactions_created_at ON fx_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fx_transactions_correlation ON fx_transactions(correlation_id);
