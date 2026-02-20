"""
Main tracer interface for Beryl Core API observability.
"""

from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from src.observability.tracing.opentelemetry import tracer as otel_tracer

try:  # pragma: no cover
    from opentelemetry import trace
except ModuleNotFoundError:  # pragma: no cover
    class _NoopSpan:
        @staticmethod
        def is_recording() -> bool:
            return False

    class _NoopTrace:
        @staticmethod
        def get_current_span():
            return _NoopSpan()

    trace = _NoopTrace()


class BerylTracer:
    """
    Main tracer interface providing convenient methods for tracing.
    """

    def __init__(self):
        self.otel_tracer = otel_tracer

    @contextmanager
    def trace_http_request(self, method: str, path: str,
                          user_id: Optional[str] = None) -> Generator[Any, None, None]:
        """Context manager for HTTP request tracing."""
        span = self.otel_tracer.start_http_span(method, path, user_id)
        try:
            yield span
            self.otel_tracer.set_span_success(span)
        except Exception as e:
            self.otel_tracer.record_exception(span, e)
            raise
        finally:
            span.end()

    @contextmanager
    def trace_business_operation(self, domain: str, operation: str,
                               attributes: Optional[Dict[str, Any]] = None) -> Generator[Any, None, None]:
        """Context manager for business operation tracing."""
        span = self.otel_tracer.start_business_span(domain, operation, attributes)
        try:
            yield span
            self.otel_tracer.set_span_success(span)
        except Exception as e:
            self.otel_tracer.record_exception(span, e)
            raise
        finally:
            span.end()

    @contextmanager
    def trace_adapter_call(self, adapter: str, method: str) -> Generator[Any, None, None]:
        """Context manager for adapter call tracing."""
        span = self.otel_tracer.start_adapter_span(adapter, method)
        try:
            yield span
            self.otel_tracer.set_span_success(span)
        except Exception as e:
            self.otel_tracer.record_exception(span, e)
            raise
        finally:
            span.end()

    @contextmanager
    def trace_event_operation(self, event_type: str, operation: str = "publish") -> Generator[Any, None, None]:
        """Context manager for event operation tracing."""
        span = self.otel_tracer.start_event_span(event_type, operation)
        try:
            yield span
            self.otel_tracer.set_span_success(span)
        except Exception as e:
            self.otel_tracer.record_exception(span, e)
            raise
        finally:
            span.end()

    @contextmanager
    def trace_graphql_operation(self, operation_type: str, operation_name: str) -> Generator[Any, None, None]:
        """Context manager for GraphQL operation tracing."""
        span = self.otel_tracer.start_graphql_span(operation_type, operation_name)
        try:
            yield span
            self.otel_tracer.set_span_success(span)
        except Exception as e:
            self.otel_tracer.record_exception(span, e)
            raise
        finally:
            span.end()

    def start_custom_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Start a custom span manually."""
        return self.otel_tracer.start_span(name, attributes=attributes)

    def add_attributes_to_current_span(self, attributes: Dict[str, Any]):
        """Add attributes to the currently active span."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            self.otel_tracer.add_span_attributes(current_span, attributes)


# Global tracer instance
tracer = BerylTracer()
