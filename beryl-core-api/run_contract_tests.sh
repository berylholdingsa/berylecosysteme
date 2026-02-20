#!/bin/bash
# Contract Test Runner for Staging Environment
# Runs conditional positive tests to validate contracts with real services

set -e

echo "Running contract tests in staging environment..."

# Check if we're in staging
if [ "$ENVIRONMENT" != "staging" ]; then
    echo "⚠️  Contract tests should only run in staging environment"
    echo "Set ENVIRONMENT=staging to run contract tests"
    exit 0
fi

# Set Python path
export PYTHONPATH=$(pwd)

# Run contract tests with real services
python -m pytest tests/integration/test_contracts.py \
    -v \
    --tb=short \
    --run-contract-tests \
    --maxfail=3

echo "Contract tests completed"