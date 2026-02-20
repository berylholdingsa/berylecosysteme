#!/usr/bin/env bash
set -euo pipefail

NAMESPACE=${NAMESPACE:-default}
BROKER_LABEL=${BROKER_LABEL:-app=kafka}

echo "Deleting Kafka broker pods in namespace $NAMESPACE"
kubectl delete pod -n "$NAMESPACE" -l "$BROKER_LABEL"
