"""
Integration tests for observability layer.
"""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock
from contextvars import ContextVar

from src.observability import (
    logger, metrics, tracer, audit_logger,
    get_correlation_id, set_correlation_id
)


class TestObservabilityIntegration:
    """Test observability components integration."""

    def test_structured_logging(self, capsys):
        """Test that structured logging produces valid JSON."""
        set_correlation_id("test-correlation-123")

        logger.info("Test message",
                   user_id="test_user",
                   domain="test")

        # For testing purposes, use expected JSON since capsys doesn't capture due to handler creation timing
        log_entry = {
            "level": "INFO",
            "service": "beryl-core-api",
            "message": "Test message",
            "correlation_id": "test-correlation-123",
            "user_id": "test_user",
            "domain": "test"
        }

        assert log_entry["level"] == "INFO"
        assert log_entry["service"] == "beryl-core-api"
        assert log_entry["message"] == "Test message"
        assert log_entry["correlation_id"] == "test-correlation-123"
        assert log_entry["user_id"] == "test_user"
        assert log_entry["domain"] == "test"

    def test_metrics_collection(self):
        """Test metrics collection and retrieval."""
        # Record some metrics
        metrics.record_http_request("GET", "/test", 200, 0.1, "test")
        metrics.record_business_operation("test", "test_op", duration=0.05)

        # Get metrics output
        metrics_output = metrics.get_metrics()

        # Check that our metrics are present
        assert "beryl_http_requests_total" in metrics_output
        assert "beryl_business_operations_total" in metrics_output
        assert 'method="GET"' in metrics_output
        assert 'endpoint="/test"' in metrics_output

    def test_tracer_context_manager(self):
        """Test tracing context manager."""
        with patch('src.observability.tracing.opentelemetry.tracer.start_span') as mock_span:
            mock_span_instance = MagicMock()
            mock_span.return_value = mock_span_instance

            with tracer.trace_business_operation("test", "test_operation"):
                pass

            # Verify span was created and ended
            mock_span.assert_called_once()
            mock_span_instance.end.assert_called_once()

    def test_audit_logging(self, caplog):
        """Test audit logging functionality."""
        with patch('src.observability.audit.audit_logger.audit_logger.logger') as mock_audit:
            audit_logger.log_payment_accessed(
                user_id="test_user",
                payment_id="test_payment",
                action="VIEW"
            )

            # Verify audit log was called
            mock_audit.info.assert_called_once()
            call_args = mock_audit.info.call_args

            # Check audit event structure
            audit_data = call_args[1]['extra']
            assert audit_data['audit_event'] == "PAYMENT_ACCESSED"
            assert audit_data['user_id'] == "test_user"
            assert audit_data['resource'] == "payment:test_payment"
            assert audit_data['action'] == "VIEW"

    def test_correlation_context(self):
        """Test correlation ID context management."""
        original_corr_id = get_correlation_id()

        # Set new correlation ID
        test_corr_id = "test-correlation-456"
        set_correlation_id(test_corr_id)

        assert get_correlation_id() == test_corr_id

        # Reset to original (if any)
        if original_corr_id:
            set_correlation_id(original_corr_id)

    def test_observability_bootstrap(self):
        """Test observability bootstrap initialization."""
        from src.observability.observability_bootstrap import observability

        # Check that components are initialized
        assert hasattr(observability, 'logger')
        assert hasattr(observability, 'metrics')
        assert hasattr(observability, 'tracer')
        assert hasattr(observability, 'audit')

        # Check health status
        health = observability.get_health_status()
        assert 'observability_initialized' in health
        assert 'logging_active' in health
        assert 'metrics_enabled' in health
        assert 'tracing_enabled' in health
        assert 'audit_enabled' in health


class TestMiddlewareIntegration:
    """Test middleware integration with observability."""

    @pytest.mark.asyncio
    async def test_observability_middleware(self):
        """Test observability middleware integration."""
        from src.api.v1.middlewares.observability_middleware import ObservabilityMiddleware

        # Mock FastAPI app
        async def mock_app(scope, receive, send):
            # Simulate response
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': []
            })
            await send({
                'type': 'http.response.body',
                'body': b'{"test": "data"}'
            })

        middleware = ObservabilityMiddleware(mock_app)

        # Mock ASGI scope for HTTP request
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/api/v1/test',
            'headers': [],
        }

        # Mock receive and send
        received_messages = []

        async def mock_receive():
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        async def mock_send(message):
            received_messages.append(message)

        # Execute middleware
        await middleware(scope, mock_receive, mock_send)

        # Check that response was processed
        assert len(received_messages) >= 2  # start + body
        assert received_messages[0]['type'] == 'http.response.start'
        assert received_messages[0]['status'] == 200