#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROTATION_INTERVAL_DAYS="${ROTATION_INTERVAL_DAYS:-90}"
STATE_FILE="${KEY_ROTATION_STATE_FILE:-${ROOT_DIR}/infra/.key-rotation-state.json}"
SECRETS_BACKEND="${SECRETS_BACKEND:-mock}"
MOCK_SECRETS_FILE="${MOCK_SECRETS_FILE:-/tmp/beryl-mock-secrets-store.json}"
VAULT_SECRET_PATH="${VAULT_SECRET_PATH:-secret/data/beryl-core-api/keys/active}"
SIMULATE="${SIMULATE:-false}"
FORCE_ROTATE="${FORCE_ROTATE:-false}"

mkdir -p "$(dirname "${STATE_FILE}")"

log_json() {
  local event="$1"
  local status="$2"
  local message="$3"
  printf '{"event":"%s","status":"%s","message":"%s","timestamp":"%s"}\n' \
    "$event" "$status" "$message" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

read_last_rotation_epoch() {
  if [[ ! -f "${STATE_FILE}" ]]; then
    echo 0
    return
  fi
  python3 - "${STATE_FILE}" <<'PY'
import json
import sys
from pathlib import Path

state_file = Path(sys.argv[1])
try:
    data = json.loads(state_file.read_text(encoding="utf-8"))
    print(int(data.get("rotated_at_epoch", 0)))
except Exception:
    print(0)
PY
}

write_state() {
  local rotated_at_epoch="$1"
  local next_rotation_epoch="$2"
  cat > "${STATE_FILE}" <<JSON
{
  "rotation_interval_days": ${ROTATION_INTERVAL_DAYS},
  "rotated_at_epoch": ${rotated_at_epoch},
  "next_rotation_epoch": ${next_rotation_epoch},
  "backend": "${SECRETS_BACKEND}"
}
JSON
}

store_secret() {
  local new_key="$1"

  if [[ "${SIMULATE}" == "true" ]]; then
    log_json "key_rotation" "simulated" "simulation mode enabled"
    return
  fi

  if [[ "${SECRETS_BACKEND}" == "vault" ]]; then
    if ! command -v vault >/dev/null 2>&1; then
      log_json "key_rotation" "error" "vault CLI not found"
      return 1
    fi
    vault kv put "${VAULT_SECRET_PATH}" \
      audit_hmac_key="${new_key}" \
      rotated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" >/dev/null
    log_json "key_rotation" "ok" "stored secret via vault"
    return
  fi

  cat > "${MOCK_SECRETS_FILE}" <<JSON
{
  "backend": "mock",
  "path": "${VAULT_SECRET_PATH}",
  "audit_hmac_key": "${new_key}",
  "rotated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON
  chmod 600 "${MOCK_SECRETS_FILE}"
  log_json "key_rotation" "ok" "stored secret in mock backend"
}

now_epoch="$(date +%s)"
last_rotation_epoch="$(read_last_rotation_epoch)"

if [[ "${last_rotation_epoch}" -gt 0 ]]; then
  days_since=$(( (now_epoch - last_rotation_epoch) / 86400 ))
else
  days_since=9999
fi

if [[ "${FORCE_ROTATE}" != "true" && "${days_since}" -lt "${ROTATION_INTERVAL_DAYS}" ]]; then
  log_json "key_rotation" "skipped" "rotation interval not reached"
  exit 0
fi

if ! command -v openssl >/dev/null 2>&1; then
  log_json "key_rotation" "error" "openssl not found"
  exit 1
fi

new_key="$(openssl rand -hex 32)"
next_rotation_epoch=$(( now_epoch + ROTATION_INTERVAL_DAYS * 86400 ))

store_secret "${new_key}"
write_state "${now_epoch}" "${next_rotation_epoch}"

log_json "key_rotation" "rotated" "automatic 90-day key rotation completed"
