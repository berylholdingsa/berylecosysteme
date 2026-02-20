# Secure Deployment Instructions

## 1. Mandatory Environment Variables
- `DATABASE_URL`
- `JWT_SIGNING_KEYS_JSON`
- `JWT_ACTIVE_KID`
- `EVENT_HMAC_SECRET`
- `PSP_WEBHOOK_HMAC_SECRET`
- `AES256_KEY_B64` (32-byte key, base64)
- `AUDIT_SECRET_KEY`
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_MANUAL_COMMIT_ONLY=true`
- `KAFKA_REQUIRED_SIGNED_TOPICS`
- `REDIS_URL`

## 2. Transport and Gateway
- Enforce HTTPS end-to-end (`ENFORCE_TLS=true`).
- Configure trusted reverse proxy to set `X-Forwarded-Proto`.
- Restrict CORS origins (`CORS_ALLOWED_ORIGINS`).

## 3. Database and Migrations
- Apply SQL migrations through `db/migrations` in order.
- Validate append-only audit triggers in production.
- Verify backup and PITR before go-live.

## 4. Kafka
- Pre-create primary and DLQ topics.
- Apply retention policy for DLQ topics.
- Verify consumer group naming by environment.

## 5. Verification Checklist
- `GET /health` returns healthy.
- `GET /metrics` exposes compliance metrics.
- `GET /api/v1/fintech/audit/verify` returns `ok=true`.
- Run `python tools/ArchitectureAudit.py --strict --require-score 100`.
