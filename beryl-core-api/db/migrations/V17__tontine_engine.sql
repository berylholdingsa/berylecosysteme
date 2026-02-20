CREATE TABLE IF NOT EXISTS tontine_groups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  community_group_id TEXT NOT NULL,
  contribution_amount NUMERIC(18,2) NOT NULL,
  frequency_type TEXT NOT NULL CHECK (frequency_type IN ('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY')),
  max_members INTEGER NOT NULL CHECK (max_members >= 2 AND max_members <= 10),
  security_code_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  signature_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tontine_groups_community
  ON tontine_groups(community_group_id);

CREATE TABLE IF NOT EXISTS tontine_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tontine_id UUID NOT NULL REFERENCES tontine_groups(id),
  user_id TEXT NOT NULL,
  reputation_score NUMERIC(5,2) NOT NULL DEFAULT 50.00 CHECK (reputation_score >= 0 AND reputation_score <= 100),
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_tontine_member UNIQUE (tontine_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tontine_members_tontine
  ON tontine_members(tontine_id);

CREATE INDEX IF NOT EXISTS idx_tontine_members_user
  ON tontine_members(user_id);

CREATE TABLE IF NOT EXISTS tontine_cycles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tontine_id UUID NOT NULL REFERENCES tontine_groups(id),
  cycle_number INTEGER NOT NULL,
  total_pool NUMERIC(18,2) NOT NULL DEFAULT 0.00,
  next_distribution_date TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  commission_total NUMERIC(18,2) NOT NULL DEFAULT 0.00,
  CONSTRAINT uq_tontine_cycle_number UNIQUE (tontine_id, cycle_number)
);

CREATE INDEX IF NOT EXISTS idx_tontine_cycles_tontine_status
  ON tontine_cycles(tontine_id, status);

CREATE TABLE IF NOT EXISTS tontine_withdraw_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tontine_id UUID NOT NULL REFERENCES tontine_groups(id),
  requested_by TEXT NOT NULL,
  amount NUMERIC(18,2) NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tontine_withdraw_requests_tontine
  ON tontine_withdraw_requests(tontine_id, status);

CREATE TABLE IF NOT EXISTS tontine_votes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tontine_id UUID NOT NULL REFERENCES tontine_groups(id),
  withdraw_request_id UUID NOT NULL REFERENCES tontine_withdraw_requests(id),
  user_id TEXT NOT NULL,
  approved BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_tontine_vote_unique UNIQUE (withdraw_request_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tontine_votes_withdraw
  ON tontine_votes(withdraw_request_id);
