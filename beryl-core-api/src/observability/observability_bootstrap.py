"""
Observability bootstrap module for centralized initialization.

Initializes logging, metrics, tracing, and audit systems based on configuration.
"""

import os
import logging
from typing import Optional
from pathlib import Path

from src.config.settings import settings
from src.observability.logging.logger import logger as beryl_logger
from src.observability.metrics.prometheus import metrics as beryl_metrics
from src.observability.tracing.tracer import tracer as beryl_tracer
from src.observability.audit.audit_logger import audit_logger as beryl_audit


class ObservabilityBootstrap:
    """
    Centralized observability initialization and configuration.
    """

    def __init__(self):
        self._initialized = False
        self.logger = beryl_logger
        self.metrics = beryl_metrics
        self.tracer = beryl_tracer
        self.audit = beryl_audit

    def initialize(self):
        """Initialize all observability components."""
        if self._initialized:
            return

        try:
            # Set global log level
            self._configure_logging()

            # Initialize components based on environment
            self._initialize_metrics()
            self._initialize_tracing()
            self._initialize_audit()

            self._initialized = True
            self.logger.info("Observability system initialized successfully",
                           environment=settings.environment,
                           tracing_enabled=settings.tracing_enabled,
                           metrics_enabled=settings.metrics_enabled)

        except Exception as e:
            self.logger.error(
                "event=observability_initialization_failed",
                error=str(e),
            )

    def _configure_logging(self):
        """Configure global logging level."""
        log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)

        # Set specific log levels for noisy libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('opentelemetry').setLevel(logging.WARNING)
        logging.getLogger('prometheus_client').setLevel(logging.WARNING)

    def _initialize_metrics(self):
        """Initialize metrics collection."""
        if not settings.metrics_enabled:
            self.logger.info("Metrics collection disabled")
            return

        try:
            # Metrics are initialized at import time
            self.logger.info("Metrics collection initialized",
                           metrics_endpoint="/metrics")
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics: {e}")

    def _initialize_tracing(self):
        """Initialize distributed tracing."""
        if not settings.tracing_enabled:
            self.logger.info("Distributed tracing disabled")
            return

        try:
            # Tracing is initialized at import time
            exporters = []
            if settings.jaeger_endpoint:
                exporters.append("Jaeger")
            if settings.zipkin_endpoint:
                exporters.append("Zipkin")

            self.logger.info("Distributed tracing initialized",
                           exporters=exporters if exporters else ["None"])
        except Exception as e:
            self.logger.error(f"Failed to initialize tracing: {e}")

    def _initialize_audit(self):
        """Initialize audit logging."""
        if not settings.audit_enabled:
            self.logger.info("Audit logging disabled")
            return

        try:
            # Ensure audit log directory exists
            audit_log_path = Path(settings.audit_log_file)
            if audit_log_path.parent and str(audit_log_path.parent) not in {".", ""}:
                audit_log_path.parent.mkdir(parents=True, exist_ok=True)

            self.logger.info("Audit logging initialized",
                           audit_log_file=str(audit_log_path))
        except Exception as e:
            self.logger.error(f"Failed to initialize audit logging: {e}")

    def get_health_status(self) -> dict:
        """Get observability system health status."""
        return {
            "observability_initialized": self._initialized,
            "logging_active": True,  # Always active
            "metrics_enabled": settings.metrics_enabled,
            "tracing_enabled": settings.tracing_enabled,
            "audit_enabled": settings.audit_enabled,
            "environment": settings.environment,
        }

    def shutdown(self):
        """Gracefully shutdown observability components."""
        try:
            self.logger.info("Shutting down observability system")
            # Add cleanup logic here if needed
            self._initialized = False
        except Exception as e:
            self.logger.error(
                "event=observability_shutdown_failed",
                error=str(e),
            )


# Global bootstrap instance
observability = ObservabilityBootstrap()


def init_observability():
    """Convenience function to initialize observability."""
    observability.initialize()


def get_observability_status() -> dict:
    """Convenience function to get observability status."""
    return observability.get_health_status()
