#!/usr/bin/env bash
set -euo pipefail

NAMESPACE=${NAMESPACE:-default}
DB_LABEL=${DB_LABEL:-app=postgres}

echo "Deleting DB pod to simulate temporary loss"
kubectl delete pod -n "$NAMESPACE" -l "$DB_LABEL"
