CREATE TABLE IF NOT EXISTS saved_beneficiaries (
    id UUID PRIMARY KEY,
    owner_uid TEXT NOT NULL,
    beneficiary_account_id TEXT NOT NULL,
    nickname TEXT,
    last_used_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_owner_beneficiary UNIQUE (owner_uid, beneficiary_account_id)
);
