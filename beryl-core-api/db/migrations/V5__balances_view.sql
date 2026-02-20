CREATE OR REPLACE VIEW account_balances AS
SELECT
  a.id AS account_id,
  a.user_id,
  a.currency,
  COALESCE(SUM(
    CASE
      WHEN e.direction = 'CREDIT' THEN e.amount
      WHEN e.direction = 'DEBIT' THEN -e.amount
    END
  ), 0) AS balance
FROM accounts a
LEFT JOIN ledger_entries e ON e.account_id = a.id
GROUP BY a.id, a.user_id, a.currency;
