# Central Security Journal

Security-relevant events are centralized through:
- structured JSON application logger (`src/observability/logging/logger.py`)
- immutable audit chain (`src/core/audit`)
- Prometheus incident counters (`security_incident_total`, `signature_validation_failures_total`)

## Mandatory Event Types
- Authentication failures
- Authorization denials
- Replay attack rejections
- Signature validation failures
- AML flagged transactions
- Audit integrity failures
