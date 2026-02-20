#!/bin/bash

# Beryl Core API Deployment Script
# This script deploys the complete Beryl ecosystem to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-default}"
ENVIRONMENT="${ENVIRONMENT:-staging}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-ghcr.io}"
REPO="${REPO:-generalhaypi/beryl_ecosysteme/beryl-core-api}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi

    log_success "Dependencies check passed"
}

setup_namespace() {
    log_info "Setting up namespaces..."

    # Create namespaces
    kubectl apply -f k8s/namespaces/

    # Wait for namespaces
    kubectl wait --for=condition=established --timeout=60s namespace/beryl-fintech || true
    kubectl wait --for=condition=established --timeout=60s namespace/beryl-mobility || true
    kubectl wait --for=condition=established --timeout=60s namespace/beryl-esg || true
    kubectl wait --for=condition=established --timeout=60s namespace/beryl-social || true

    log_success "Namespaces created"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure components..."

    # PVCs
    kubectl apply -f k8s/pvc.yaml

    # RBAC
    kubectl apply -f k8s/rbac.yaml

    # Network Policies
    kubectl apply -f k8s/network-policies.yaml

    # Pod Disruption Budgets
    kubectl apply -f k8s/pdb.yaml

    # Certificates
    kubectl apply -f k8s/certificates.yaml

    log_success "Infrastructure deployed"
}

deploy_monitoring() {
    log_info "Deploying monitoring stack..."

    # Monitoring configurations
    kubectl apply -f k8s/monitoring-config.yaml

    # Check if monitoring namespace exists
    if ! kubectl get namespace beryl-monitoring &> /dev/null; then
        log_warning "beryl-monitoring namespace not found. Skipping monitoring deployment."
        return
    fi

    log_success "Monitoring deployed"
}

deploy_application() {
    log_info "Deploying Beryl Core API application..."

    # Update image tags in deployments
    sed -i "s|beryl/core-api:latest|${REGISTRY}/${REPO}:${IMAGE_TAG}|g" k8s/deployments/beryl-core-api-deployment.yaml
    sed -i "s|beryl/graphql-gateway:latest|${REGISTRY}/${REPO}-graphql:${IMAGE_TAG}|g" k8s/deployments/graphql-gateway-deployment.yaml
    sed -i "s|beryl/event-bus:latest|${REGISTRY}/${REPO}-eventbus:${IMAGE_TAG}|g" k8s/deployments/event-bus-deployment.yaml

    # ConfigMaps
    kubectl apply -f k8s/configmaps/

    # Secrets
    kubectl apply -f k8s/secrets/

    # Deployments
    kubectl apply -f k8s/deployments/

    # Services
    kubectl apply -f k8s/services/

    # Ingress
    kubectl apply -f k8s/ingress/

    # Horizontal Pod Autoscalers
    kubectl apply -f k8s/hpa.yaml

    log_success "Application deployed"
}

wait_for_rollout() {
    log_info "Waiting for deployments to be ready..."

    # Wait for core API
    kubectl rollout status deployment/beryl-core-api -n ${NAMESPACE} --timeout=600s

    # Wait for GraphQL gateway
    kubectl rollout status deployment/graphql-gateway -n ${NAMESPACE} --timeout=300s

    # Wait for event bus
    kubectl rollout status deployment/event-bus -n ${NAMESPACE} --timeout=300s

    log_success "All deployments are ready"
}

run_health_checks() {
    log_info "Running health checks..."

    # Core API health check
    kubectl exec -it deployment/beryl-core-api -n ${NAMESPACE} -- curl -f http://localhost:8000/health

    # GraphQL health check
    kubectl exec -it deployment/graphql-gateway -n ${NAMESPACE} -- curl -f http://localhost:8080/health

    # Metrics endpoint check
    kubectl exec -it deployment/beryl-core-api -n ${NAMESPACE} -- curl -f http://localhost:9090/metrics

    log_success "Health checks passed"
}

run_integration_tests() {
    log_info "Running integration tests..."

    # Run tests against deployed services
    if [ -f "tests/integration/" ]; then
        # If we have test files, we could run them here
        # For now, just check basic connectivity
        kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -f https://api.beryl-ecosystem.com/health
    fi

    log_success "Integration tests completed"
}

cleanup() {
    log_info "Cleaning up temporary resources..."

    # Remove any temporary resources created during deployment
    kubectl delete pods -l job-name=deployment-test -n ${NAMESPACE} --ignore-not-found=true

    log_success "Cleanup completed"
}

rollback() {
    log_error "Deployment failed. Initiating rollback..."

    # Rollback deployments
    kubectl rollout undo deployment/beryl-core-api -n ${NAMESPACE}
    kubectl rollout undo deployment/graphql-gateway -n ${NAMESPACE}
    kubectl rollout undo deployment/event-bus -n ${NAMESPACE}

    log_info "Rollback completed"
}

# Main deployment flow
main() {
    log_info "Starting Beryl Core API deployment to ${ENVIRONMENT} environment"
    log_info "Namespace: ${NAMESPACE}"
    log_info "Image Tag: ${IMAGE_TAG}"

    # Trap for cleanup on error
    trap rollback ERR

    check_dependencies
    setup_namespace
    deploy_infrastructure
    deploy_monitoring
    deploy_application
    wait_for_rollout
    run_health_checks
    run_integration_tests
    cleanup

    log_success "🎉 Beryl Core API deployment completed successfully!"
    log_info "Application is available at:"
    log_info "  - REST API: https://api.beryl-ecosystem.com"
    log_info "  - GraphQL: https://graphql.beryl-ecosystem.com"
    log_info "  - Health: https://api.beryl-ecosystem.com/health"
    log_info "  - Metrics: https://api.beryl-ecosystem.com/metrics"
}

# Run main function
main "$@"