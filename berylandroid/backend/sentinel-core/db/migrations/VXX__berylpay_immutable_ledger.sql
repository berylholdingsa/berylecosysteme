CREATE TABLE IF NOT EXISTS beryl_pay_ledger (
    id UUID PRIMARY KEY,
    account_id TEXT NOT NULL,
    type TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    request_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    nonce TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    hash TEXT NOT NULL
);

CREATE OR REPLACE FUNCTION prevent_ledger_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'Ledger is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ledger_no_update ON beryl_pay_ledger;
CREATE TRIGGER ledger_no_update
BEFORE UPDATE OR DELETE ON beryl_pay_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
