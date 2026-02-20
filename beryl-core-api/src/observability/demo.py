"""
Observability usage examples and demonstrations.

This module shows how to integrate observability features throughout the application.
"""

import time
from typing import Optional

from src.observability import (
    logger, metrics, counters, histograms, tracer, audit_logger,
    get_correlation_id, set_domain
)


class ObservabilityDemo:
    """
    Demonstration of observability features integration.
    """

    @staticmethod
    def demo_logging():
        """Demonstrate structured logging."""
        logger.info("Demo: Structured logging example",
                   user_id="user123",
                   action="demo_logging",
                   extra_data={"feature": "observability"})

        logger.warning("Demo: Warning with correlation",
                      correlation_id=get_correlation_id(),
                      warning_type="demo")

    @staticmethod
    def demo_metrics():
        """Demonstrate metrics collection."""
        # HTTP request metrics
        metrics.record_http_request("GET", "/api/v1/demo", 200, 0.1, "demo")

        # Business operation metrics
        metrics.record_business_operation("demo", "test_operation", duration=0.05)

        # Custom counters
        counters.increment_fintech_operation("demo_payment", currency="EUR")

        # Custom histograms
        histograms.observe_fintech_operation("demo_transaction", 0.02)

    @staticmethod
    def demo_tracing():
        """Demonstrate distributed tracing."""
        with tracer.trace_business_operation("demo", "tracing_example") as span:
            # Add custom attributes
            tracer.add_attributes_to_current_span({
                "demo.operation": "tracing_example",
                "demo.version": "1.0"
            })

            # Simulate some work
            time.sleep(0.01)

            # Nested span
            with tracer.trace_adapter_call("demo_adapter", "test_method"):
                time.sleep(0.005)

    @staticmethod
    def demo_audit():
        """Demonstrate audit logging."""
        audit_logger.log_payment_accessed(
            user_id="demo_user",
            payment_id="demo_payment_123",
            action="VIEW",
            ip_address="127.0.0.1"
        )

        audit_logger.log_health_data_accessed(
            user_id="demo_user",
            data_type="pedometer",
            action="READ",
            ip_address="127.0.0.1"
        )

    @staticmethod
    def demo_correlation():
        """Demonstrate correlation ID management."""
        set_domain("demo")

        logger.info("Demo: Correlation tracking",
                   correlation_id=get_correlation_id(),
                   domain="demo")

    @staticmethod
    def run_full_demo():
        """Run complete observability demonstration."""
        logger.info("event=observability_demo_started")

        set_domain("demo")

        # Logging demo
        logger.info("event=observability_demo_step step=logging")
        ObservabilityDemo.demo_logging()

        # Metrics demo
        logger.info("event=observability_demo_step step=metrics")
        ObservabilityDemo.demo_metrics()

        # Tracing demo
        logger.info("event=observability_demo_step step=tracing")
        ObservabilityDemo.demo_tracing()

        # Audit demo
        logger.info("event=observability_demo_step step=audit")
        ObservabilityDemo.demo_audit()

        # Correlation demo
        logger.info("event=observability_demo_step step=correlation")
        ObservabilityDemo.demo_correlation()

        logger.info("event=observability_demo_completed")


# Convenience function for quick demo
def run_observability_demo():
    """Run the observability demonstration."""
    ObservabilityDemo.run_full_demo()
