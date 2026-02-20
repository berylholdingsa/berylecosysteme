CREATE TABLE IF NOT EXISTS suspicious_activity_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  risk_score NUMERIC(6,2) NOT NULL,
  reasons TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_suspicious_activity_tx ON suspicious_activity_logs(transaction_id);
CREATE INDEX IF NOT EXISTS idx_suspicious_activity_actor ON suspicious_activity_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_suspicious_activity_created ON suspicious_activity_logs(created_at DESC);
