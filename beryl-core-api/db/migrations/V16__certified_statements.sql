CREATE TABLE IF NOT EXISTS certified_statements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  statement_id TEXT NOT NULL UNIQUE,
  user_id TEXT NOT NULL,
  merchant_name TEXT NOT NULL,
  period_label TEXT NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  total_sales NUMERIC(18,2) NOT NULL,
  total_charges NUMERIC(18,2) NOT NULL,
  net_result NUMERIC(18,2) NOT NULL,
  cashflow NUMERIC(18,2) NOT NULL,
  statement_fee NUMERIC(18,2) NOT NULL,
  currency TEXT NOT NULL,
  pdf_blob BYTEA NOT NULL,
  pdf_hash TEXT NOT NULL UNIQUE,
  embedded_hash TEXT NOT NULL,
  signature TEXT NOT NULL,
  signature_algorithm TEXT NOT NULL,
  signature_key_id TEXT NOT NULL,
  verification_url TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  revenue_record_id TEXT,
  immutable BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_certified_statements_user_created
  ON certified_statements(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_certified_statements_period
  ON certified_statements(period_start, period_end);

CREATE TABLE IF NOT EXISTS statement_signatures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  statement_ref UUID NOT NULL REFERENCES certified_statements(id),
  signed_hash TEXT NOT NULL,
  signature TEXT NOT NULL,
  algorithm TEXT NOT NULL,
  public_key_pem TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_statement_signatures_statement_ref
  ON statement_signatures(statement_ref);
