#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_PATH="${REPORT_PATH:-${ROOT_DIR}/staging/reports/staging_compliance_report.json}"
SUITE_MODE="${SUITE_MODE:-simulation}"

mkdir -p "$(dirname "${REPORT_PATH}")"

if command -v poetry >/dev/null 2>&1 && [[ -f "${ROOT_DIR}/pyproject.toml" ]]; then
  TEST_RUNNER=(poetry run pytest -q)
else
  TEST_RUNNER=(python3 -m pytest -q)
fi

RESULTS_FILE="$(mktemp)"
trap 'rm -f "${RESULTS_FILE}"' EXIT

log_json() {
  local event="$1"
  local status="$2"
  local detail="$3"
  printf '{"event":"%s","status":"%s","detail":"%s","timestamp":"%s"}\n' \
    "$event" "$status" "$detail" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

append_result() {
  local name="$1"
  local status="$2"
  local duration_ms="$3"
  local command="$4"
  local output_file="$5"

  python3 - "${RESULTS_FILE}" "${name}" "${status}" "${duration_ms}" "${command}" "${output_file}" <<'PY'
import json
import sys
from pathlib import Path

results_file = Path(sys.argv[1])
name = sys.argv[2]
status = sys.argv[3]
duration_ms = int(sys.argv[4])
command = sys.argv[5]
output_file = Path(sys.argv[6])
output = output_file.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
result = {
    "name": name,
    "status": status,
    "duration_ms": duration_ms,
    "command": command,
    "output_tail": output[-20:],
}
with results_file.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(result, ensure_ascii=True) + "\n")
PY
}

run_step() {
  local name="$1"
  shift
  local cmd=("$@")
  local out_file
  out_file="$(mktemp)"

  local start_ms end_ms duration status
  start_ms="$(date +%s%3N)"
  if "${cmd[@]}" >"${out_file}" 2>&1; then
    status="passed"
    log_json "${name}" "passed" "step completed"
  else
    status="failed"
    log_json "${name}" "failed" "step failed"
  fi
  end_ms="$(date +%s%3N)"
  duration=$((end_ms - start_ms))

  append_result "${name}" "${status}" "${duration}" "${cmd[*]}" "${out_file}"
  rm -f "${out_file}"

  [[ "${status}" == "passed" ]]
}

validate_dataset() {
  local required=(
    "staging/seed_data_anonymized.json"
    "staging/simulated_transactions.json"
    "staging/aml_cases_positifs_negatifs.json"
    "staging/psp_replay_scenarios.json"
    "staging/fraud_test_scenarios.json"
  )
  local missing=0
  for rel in "${required[@]}"; do
    if [[ ! -f "${ROOT_DIR}/${rel}" ]]; then
      missing=1
    fi
  done
  if [[ "${missing}" -eq 0 ]]; then
    log_json "dataset_validation" "passed" "all staging datasets found"
    return 0
  fi
  log_json "dataset_validation" "failed" "missing staging datasets"
  return 1
}

suite_failed=0

if validate_dataset; then
  append_result "dataset_validation" "passed" 0 "validate_dataset" /dev/null
else
  append_result "dataset_validation" "failed" 0 "validate_dataset" /dev/null
  suite_failed=1
fi

if ! run_step "chaos_test" "${TEST_RUNNER[@]}" tests/regulatory/test_chaos_scenarios.py; then
  suite_failed=1
fi
if ! run_step "compliance_test" "${TEST_RUNNER[@]}" tests/regulatory/test_compliance_integrity.py; then
  suite_failed=1
fi
if ! run_step "audit_integrity_test" "${TEST_RUNNER[@]}" tests/regulatory/test_audit_chain_integrity.py; then
  suite_failed=1
fi
if ! run_step "risk_scoring_test" "${TEST_RUNNER[@]}" tests/regulatory/test_compliance_integrity.py::test_risk_scorer_flags_high_amount; then
  suite_failed=1
fi
if ! run_step "dlq_behavior_test" "${TEST_RUNNER[@]}" tests/regulatory/test_dlq_behavior.py; then
  suite_failed=1
fi

python3 - "${RESULTS_FILE}" "${REPORT_PATH}" "${SUITE_MODE}" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

results_file = Path(sys.argv[1])
report_path = Path(sys.argv[2])
suite_mode = sys.argv[3]

results = []
for line in results_file.read_text(encoding="utf-8").splitlines():
    if line.strip():
        results.append(json.loads(line))

passed = sum(1 for item in results if item.get("status") == "passed")
failed = sum(1 for item in results if item.get("status") != "passed")
score = int((passed / len(results)) * 100) if results else 0
report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "suite": "staging_regulatory_compliance",
    "mode": suite_mode,
    "score": score,
    "overall_status": "passed" if failed == 0 else "failed",
    "summary": {
        "total": len(results),
        "passed": passed,
        "failed": failed,
    },
    "checks": results,
}
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print(json.dumps({"event": "staging_suite_report", "report": str(report_path), "score": score}))
PY

if [[ "${suite_failed}" -ne 0 ]]; then
  exit 1
fi
