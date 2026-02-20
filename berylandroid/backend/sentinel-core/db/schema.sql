-- Minimal Postgres schema for BerylPay microservice and AOQ ledger.
CREATE TABLE accounts (
    id VARCHAR(64) PRIMARY KEY,
    balance DECIMAL(18,2) NOT NULL DEFAULT 0,
    currency VARCHAR(4) NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ledger_entries (
    trace_id UUID PRIMARY KEY,
    intent_name VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    services TEXT[] NOT NULL,
    requester VARCHAR(128) NOT NULL,
    timestamp BIGINT NOT NULL
);
