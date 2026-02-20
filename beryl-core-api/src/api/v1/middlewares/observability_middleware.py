"""
Observability middleware for FastAPI.

Provides comprehensive observability integration including logging, metrics,
tracing, and correlation ID management for all HTTP requests.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.errors import unified_error_response
from src.observability.logging.correlation import (
    set_correlation_id, set_request_id, set_user_id, set_domain
)
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics
from src.observability.tracing.tracer import tracer
from src.observability.audit.audit_logger import audit_logger


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for comprehensive observability.
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()

        # Setup correlation context
        correlation_id = request.headers.get("X-Correlation-ID") or getattr(request.state, "trace_id", "missing-correlation-id")
        request_id = correlation_id[:8] if correlation_id else "missing"

        set_correlation_id(correlation_id)
        set_request_id(request_id)

        # Extract user context if available
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            set_user_id(user_id)

        # Determine domain from path
        path = request.url.path
        domain = self._extract_domain_from_path(path)
        set_domain(domain)

        # Start tracing span
        with tracer.trace_http_request(
            request.method,
            path,
            user_id
        ) as span:
            try:
                # Add request attributes to span
                tracer.add_attributes_to_current_span({
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.user_agent": request.headers.get("User-Agent", ""),
                    "http.remote_ip": self._get_client_ip(request),
                    "request.id": request_id,
                    "correlation.id": correlation_id,
                })

                # Log request start
                logger.info(
                    f"HTTP {request.method} {path} - START",
                    method=request.method,
                    path=path,
                    user_id=user_id,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    domain=domain
                )

                # Process request
                response = await call_next(request)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Record metrics
                self._record_request_metrics(request, response, duration_ms, domain)

                # Log successful request
                logger.log_request(
                    request.method,
                    path,
                    response.status_code,
                    duration_ms
                )

                # Audit sensitive operations
                self._audit_request_if_needed(request, response, user_id)

                return response

            except Exception as e:
                # Calculate duration for failed requests
                duration_ms = (time.time() - start_time) * 1000

                # Record error metrics
                metrics.record_error(domain, "http_request", "middleware")
                metrics.record_http_request(
                    request.method, path, 500, duration_ms, domain
                )

                # Log error
                logger.error(
                    f"HTTP {request.method} {path} - ERROR: {str(e)}",
                    method=request.method,
                    path=path,
                    error=str(e),
                    duration_ms=duration_ms,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    domain=domain,
                    exc_info=True
                )

                # Record exception in trace
                tracer.otel_tracer.record_exception(span, e)

                # Return error response
                return unified_error_response(
                    request=request,
                    status_code=500,
                    code="INTERNAL_SERVER_ERROR",
                    message="Internal server error",
                    details={"request_id": request_id},
                )

    def _extract_domain_from_path(self, path: str) -> str:
        """Extract business domain from request path."""
        if path.startswith("/api/v1/fintech"):
            return "fintech"
        elif path.startswith("/api/v1/mobility"):
            return "mobility"
        elif path.startswith("/api/v1/esg") or path.startswith("/api/v2/esg"):
            return "esg"
        elif path.startswith("/api/v1/social"):
            return "social"
        elif path.startswith("/graphql"):
            return "graphql"
        else:
            return "unknown"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header first (for proxies/load balancers)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip

        # Fallback to direct connection
        return getattr(request.client, 'host', 'unknown') if request.client else 'unknown'

    def _record_request_metrics(self, request: Request, response: Response,
                              duration_ms: float, domain: str):
        """Record request metrics."""
        metrics.record_http_request(
            request.method,
            request.url.path,
            response.status_code,
            duration_ms / 1000,  # Convert to seconds for Prometheus
            domain
        )

    def _audit_request_if_needed(self, request: Request, response: Response, user_id: str):
        """Audit sensitive requests."""
        path = request.url.path
        method = request.method

        # Audit payment-related requests
        if path.startswith("/api/v1/fintech") and "payment" in path:
            if user_id:
                audit_logger.log_payment_accessed(
                    user_id=user_id,
                    payment_id=path.split("/")[-1] if path.endswith(tuple("0123456789")) else "unknown",
                    action=method,
                    ip_address=self._get_client_ip(request)
                )

        # Audit health data requests
        elif path.startswith("/api/v1/esg") and ("health" in path or "pedometer" in path):
            if user_id:
                audit_logger.log_health_data_accessed(
                    user_id=user_id,
                    data_type="health" if "health" in path else "pedometer",
                    action=method,
                    ip_address=self._get_client_ip(request)
                )

        # Audit wallet access
        elif path.startswith("/api/v1/fintech") and "wallet" in path:
            if user_id:
                audit_logger.log_wallet_modified(
                    user_id=user_id,
                    wallet_id=path.split("/")[-1] if path.endswith(tuple("0123456789")) else "unknown",
                    action=method,
                    amount=0.0,  # Would need to extract from request body
                    ip_address=self._get_client_ip(request)
                )


# Factory function for middleware
def create_observability_middleware(app: Callable) -> ObservabilityMiddleware:
    """Create observability middleware instance."""
    return ObservabilityMiddleware(app)
