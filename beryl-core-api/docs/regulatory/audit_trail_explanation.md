# Audit Trail Explanation

- Append-only persistence: table `audit_chain_events`.
- Each entry contains `previous_hash` + `current_hash` + `signature`.
- Chain verification endpoint: `GET /api/v1/fintech/audit/verify`.
- Read-only paginated access: `GET /api/v1/fintech/audit/events`.
