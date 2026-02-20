# Access Control Policy

## Principles
- Least privilege by default.
- Zero Trust enforcement for every request.
- Domain-scoped authorization claims.

## Role Model
- `admin`: key rotation, compliance review, audit read access.
- `operator`: operational diagnostics, non-destructive controls.
- `fintech-service`: transaction processing, outbox relay.
- `auditor`: read-only access to immutable audit endpoint.

## Enforcement
- JWT required on protected API routes.
- Scope checks for domain endpoints (`fintech`, `mobility`, `esg`, `social`, `aoq`).
- Correlation ID mandatory except health/docs endpoints.
- Nonce + timestamp required on state-changing methods.
