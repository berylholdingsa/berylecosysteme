#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000}
TOKEN=${TOKEN:-}
CORR=${CORRELATION_ID:-chaos-signature-$(date +%s)}
NONCE=${NONCE:-nonce-$(date +%s%N)}
TS=$(date +%s)

curl -sS -X POST "$API_URL/api/v1/fintech/webhooks/psp/notify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Correlation-ID: $CORR" \
  -H "X-Nonce: $NONCE" \
  -H "X-Timestamp: $TS" \
  -H "X-PSP-Signature: invalid" \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"pay-chaos-1","status":"SUCCESS"}'
