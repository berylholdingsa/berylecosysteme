#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000}
TOKEN=${TOKEN:-}
CORR=${CORRELATION_ID:-chaos-corrupt-$(date +%s)}
NONCE=${NONCE:-nonce-$(date +%s%N)}
TS=$(date +%s)

curl -sS -X POST "$API_URL/api/v1/fintech/outbox/publish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Correlation-ID: $CORR" \
  -H "X-Nonce: $NONCE" \
  -H "X-Timestamp: $TS" \
  -H "Content-Type: application/json" \
  -d '{"corrupted":"@@@not-valid-schema@@@"}'
