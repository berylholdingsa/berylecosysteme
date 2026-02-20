CREATE TABLE IF NOT EXISTS aoq_ledger_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID NOT NULL REFERENCES aoq_decisions(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  impact_type TEXT NOT NULL CHECK (impact_type IN ('credit', 'pricing', 'esg', 'matching')),
  score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 100),
  decision TEXT NOT NULL CHECK (decision IN ('APPROVE', 'REJECT')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aoq_ledger_decision_id ON aoq_ledger_entries(decision_id);
CREATE INDEX IF NOT EXISTS idx_aoq_ledger_user_id ON aoq_ledger_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_aoq_ledger_created_at ON aoq_ledger_entries(created_at DESC);

CREATE TABLE IF NOT EXISTS aoq_audit_trail (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  signature TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aoq_audit_entity_id ON aoq_audit_trail(entity_id);
CREATE INDEX IF NOT EXISTS idx_aoq_audit_created_at ON aoq_audit_trail(created_at DESC);
