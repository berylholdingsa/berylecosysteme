CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS aoq_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(128) NOT NULL UNIQUE,
  threshold DOUBLE PRECISION NOT NULL CHECK (threshold >= 0 AND threshold <= 100),
  weight_fintech DOUBLE PRECISION NOT NULL CHECK (weight_fintech >= 0 AND weight_fintech <= 1),
  weight_mobility DOUBLE PRECISION NOT NULL CHECK (weight_mobility >= 0 AND weight_mobility <= 1),
  weight_esg DOUBLE PRECISION NOT NULL CHECK (weight_esg >= 0 AND weight_esg <= 1),
  weight_social DOUBLE PRECISION NOT NULL CHECK (weight_social >= 0 AND weight_social <= 1),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aoq_rules_active ON aoq_rules(active);
CREATE INDEX IF NOT EXISTS idx_aoq_rules_updated_at ON aoq_rules(updated_at DESC);

CREATE TABLE IF NOT EXISTS aoq_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(128) NOT NULL,
  source VARCHAR(64) NOT NULL DEFAULT 'mobile',
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aoq_signals_user_id ON aoq_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_aoq_signals_created_at ON aoq_signals(created_at DESC);

CREATE TABLE IF NOT EXISTS aoq_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(128) NOT NULL,
  signal_id UUID NOT NULL REFERENCES aoq_signals(id) ON DELETE RESTRICT,
  rule_id UUID NOT NULL REFERENCES aoq_rules(id) ON DELETE RESTRICT,
  score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 100),
  threshold DOUBLE PRECISION NOT NULL CHECK (threshold >= 0 AND threshold <= 100),
  decision VARCHAR(32) NOT NULL CHECK (decision IN ('APPROVE', 'REJECT')),
  rationale TEXT NOT NULL,
  input_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aoq_decisions_user_id ON aoq_decisions(user_id);
CREATE INDEX IF NOT EXISTS idx_aoq_decisions_signal_id ON aoq_decisions(signal_id);
CREATE INDEX IF NOT EXISTS idx_aoq_decisions_created_at ON aoq_decisions(created_at DESC);
