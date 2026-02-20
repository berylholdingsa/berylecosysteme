CREATE TABLE IF NOT EXISTS account_limits (
  user_id UUID PRIMARY KEY,
  daily_limit NUMERIC(18,2) NOT NULL
);
