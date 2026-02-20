CREATE TABLE IF NOT EXISTS idempotency_keys (
  key TEXT PRIMARY KEY,
  user_id UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
