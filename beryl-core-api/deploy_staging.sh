#!/bin/bash

# Script de déploiement pour staging Beryl Core API

set -e

echo "Déploiement sur environnement staging..."

# Variables
NAMESPACE="staging"
IMAGE_TAG="latest"

# Appliquer les configurations K8s
kubectl apply -f k8s/namespaces/staging.yaml
kubectl apply -f k8s/configmaps/beryl-config.yaml
kubectl apply -f k8s/secrets/beryl-secrets.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/network-policies.yaml
kubectl apply -f k8s/zero-trust-network-policies.yaml

# Déployer l'application
kubectl set image deployment/beryl-core-api beryl-core-api=ghcr.io/your-repo/beryl-core-api:$IMAGE_TAG -n $NAMESPACE
kubectl apply -f k8s/deployments/beryl-core-api-deployment.yaml -n $NAMESPACE
kubectl apply -f k8s/services/beryl-core-api-service.yaml -n $NAMESPACE
kubectl apply -f k8s/ingress/beryl-ingress.yaml -n $NAMESPACE

# Appliquer HPA si nécessaire
kubectl apply -f k8s/hpa.yaml -n $NAMESPACE

# Attendre que le déploiement soit prêt
kubectl rollout status deployment/beryl-core-api -n $NAMESPACE

echo "Déploiement terminé. Vérifiez les logs et l'état des pods."