# Incident Handling Process

1. Detect incidents from metrics and structured logs.
2. Correlate affected requests using `X-Correlation-ID`.
3. Contain by key rotation, endpoint throttling, and consumer isolation.
4. Recover by replaying outbox safely after root cause fix.
5. Validate audit chain integrity endpoint.
6. Archive incident report with evidence hashes.
