#!/bin/bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEST_DIR="${ROOT_DIR}/tests/integration"
TEST_FILE="${TEST_DIR}/test_zero_trust_enforcement.py"
PYTEST_CMD=(pytest "${TEST_FILE}" -v --tb=short)

echo "Ensuring integration test directory exists at ${TEST_DIR}..."
mkdir -p "${TEST_DIR}"

if [[ ! -f "${TEST_FILE}" ]]; then
  echo "ERROR: ${TEST_FILE} not found; cannot validate zero-trust enforcement" >&2
  exit 1
fi

echo "Running Zero-Trust enforcement integration test..."
PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}" \
    "${PYTEST_CMD[@]}"

echo "✅ Zero-Trust enforcement tests passed; continuing deployment workflow."
