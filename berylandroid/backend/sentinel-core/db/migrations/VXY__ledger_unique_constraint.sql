ALTER TABLE beryl_pay_ledger
ADD CONSTRAINT beryl_pay_ledger_unique_request
UNIQUE (request_id, account_id, type);
