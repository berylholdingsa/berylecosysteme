#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000}
TOKEN=${TOKEN:-}
SECONDS_TO_RUN=${SECONDS_TO_RUN:-10}
TOTAL=$((2000 * SECONDS_TO_RUN))

run_one() {
  local i=$1
  local corr="chaos-flood-$i"
  local nonce="nonce-$i-$(date +%s%N)"
  local ts
  ts=$(date +%s)

  curl -sS -X POST "$API_URL/api/v1/fintech/transactions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Idempotency-Key: flood-$i" \
    -H "X-Correlation-ID: $corr" \
    -H "X-Nonce: $nonce" \
    -H "X-Timestamp: $ts" \
    -H "Content-Type: application/json" \
    -d '{"actor_id":"flood-user","amount":1.00,"currency":"XOF","target_account":"wallet-chaos"}' >/dev/null
}

export -f run_one
export API_URL TOKEN

seq 1 "$TOTAL" | xargs -P 200 -I{} bash -c 'run_one "$@"' _ {}
