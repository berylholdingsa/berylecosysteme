# Data Classification Policy

## Levels
- `Public`: marketing docs, public API references.
- `Internal`: operational logs, service metadata, deployment diagnostics.
- `Sensitive`: user profile data, auth identifiers, non-financial personal data.
- `Financial`: ledger entries, transaction details, AML indicators, audit chain evidence.

## Handling Rules
- `Public`: unrestricted read, integrity controls only.
- `Internal`: authenticated access, retention <= 365 days unless required.
- `Sensitive`: encryption in transit + at rest, least privilege access, strict audit logging.
- `Financial`: AES-256 encryption for sensitive fields, immutable audit chain, 7-year retention, signed event transport.

## Logging Policy
- Only structured JSON logs.
- No plaintext secrets/tokens.
- Correlation ID required for all protected endpoints.
