#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000}
TOKEN=${TOKEN:-}
CORR=${CORRELATION_ID:-chaos-replay-$(date +%s)}
NONCE=${NONCE:-fixed-chaos-nonce}
TS=$(date +%s)
SIG=${PSP_SIGNATURE:-invalid}
BODY='{"payment_id":"pay-replay","status":"SUCCESS"}'

for i in 1 2; do
  echo "Replay attempt $i"
  curl -sS -o /tmp/replay_$i.out -w "%{http_code}\n" -X POST "$API_URL/api/v1/fintech/webhooks/psp/notify" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Correlation-ID: $CORR" \
    -H "X-Nonce: $NONCE" \
    -H "X-Timestamp: $TS" \
    -H "X-PSP-Signature: $SIG" \
    -H "Content-Type: application/json" \
    -d "$BODY"
done
