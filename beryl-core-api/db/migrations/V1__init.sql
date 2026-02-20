-- Extensions nécessaires
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Table utilisateurs (identité interne)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table audit (socle conformité)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id
ON audit_logs(user_id);
