# Data Flow Diagram

```text
Client -> API Gateway -> Security Middleware -> Auth Middleware -> Fintech Routes
  -> Idempotency Service -> Compliance Scorer -> Audit Chain Writer -> Outbox Stage
  -> Outbox Relay -> Kafka Topic (signed + schema-validated)
                  -> DLQ Topic (invalid schema/signature failures)

Kafka Consumer (manual commit) -> Signature/Hash Verify -> Handler -> Metrics/Audit
```
