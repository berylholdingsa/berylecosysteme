# Business Continuity Plan

## Objectives
- `RTO`: 30 minutes for API critical path.
- `RPO`: 5 minutes for financial data and audit chain.

## Scenarios
- Kafka outage: route to outbox pending state, retry with exponential backoff, recover via relay replay.
- Database outage: fail write operations closed, maintain read-only status endpoints, recover from latest backup + WAL.
- Security breach: rotate JWT/HMAC keys, invalidate exposed credentials, enforce restricted mode.

## Recovery Validation
- Health endpoint green.
- Audit chain integrity verification passes.
- DLQ backlog drained and replayed with zero signature/schema violations.
