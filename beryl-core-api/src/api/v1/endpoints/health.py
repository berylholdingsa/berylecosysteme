"""
Health endpoints for the Beryl Core API.
"""

from fastapi import APIRouter, Response

from src.observability.observability_bootstrap import get_observability_status
from src.observability.metrics.prometheus import metrics

router = APIRouter()

@router.get("/")
def read_root():
    """Root endpoint for health check."""
    return {"message": "Beryl Core API is running"}

@router.get("/health")
def health_check():
    """Health check endpoint with observability status."""
    return {
        "status": "healthy",
        "service": "beryl-core-api",
        "observability": get_observability_status()
    }


@router.get("/metrics")
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(content=metrics.get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")
