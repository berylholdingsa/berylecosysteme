"""OpenTelemetry tracing integration with graceful no-op fallback."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from src.config.settings import settings
from src.infrastructure.tracing import jaeger_otlp_endpoint


class _NoopSpan:
    def set_attribute(self, *_args, **_kwargs):
        return None

    def record_exception(self, *_args, **_kwargs):
        return None

    def set_status(self, *_args, **_kwargs):
        return None

    def end(self):
        return None


class _NoopTracer:
    def start_span(self, *_args, **_kwargs):
        return _NoopSpan()


class _NoopStatusCode:
    ERROR = "ERROR"
    OK = "OK"


class _NoopStatus:
    def __init__(self, *_args, **_kwargs):
        pass


try:  # pragma: no cover - runtime optional dependency
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    trace = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    Status = _NoopStatus
    StatusCode = _NoopStatusCode
    OTEL_AVAILABLE = False


class BerylTracer:
    """OpenTelemetry tracer for distributed tracing across Beryl ecosystem."""

    def __init__(self):
        self._setup_tracer()
        if OTEL_AVAILABLE and trace is not None:
            self.tracer = trace.get_tracer(__name__)
        else:
            self.tracer = _NoopTracer()

    def _setup_tracer(self):
        """Setup OpenTelemetry tracer with optional OTLP exporter."""
        if not OTEL_AVAILABLE or trace is None or TracerProvider is None or Resource is None:
            return

        resource = Resource.create(
            {
                "service.name": "beryl-core-api",
                "service.version": "1.0.0",
                "service.environment": settings.environment,
            }
        )
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        endpoint = (
            os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            or settings.jaeger_endpoint
            or jaeger_otlp_endpoint()
        )
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

                otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except Exception:
                pass

    def start_span(self, name: str, kind: Any = None, attributes: Optional[Dict[str, Any]] = None):
        """Start a new span."""
        if kind is None and OTEL_AVAILABLE and trace is not None:
            kind = trace.SpanKind.INTERNAL
        span = self.tracer.start_span(name, kind=kind)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span

    def start_http_span(self, method: str, path: str, user_id: Optional[str] = None):
        kind = trace.SpanKind.SERVER if OTEL_AVAILABLE and trace is not None else None
        return self.start_span(
            f"HTTP {method} {path}",
            kind=kind,
            attributes={
                "http.method": method,
                "http.url": path,
                "user.id": user_id or "anonymous",
                "service.name": "beryl-core-api",
            },
        )

    def start_business_span(self, domain: str, operation: str, attributes: Optional[Dict[str, Any]] = None):
        span_attributes = {
            "business.domain": domain,
            "business.operation": operation,
        }
        if attributes:
            span_attributes.update(attributes)
        kind = trace.SpanKind.INTERNAL if OTEL_AVAILABLE and trace is not None else None
        return self.start_span(f"{domain}.{operation}", kind=kind, attributes=span_attributes)

    def start_adapter_span(self, adapter: str, method: str):
        kind = trace.SpanKind.CLIENT if OTEL_AVAILABLE and trace is not None else None
        return self.start_span(
            f"adapter.{adapter}.{method}",
            kind=kind,
            attributes={
                "adapter.name": adapter,
                "adapter.method": method,
                "span.type": "adapter",
            },
        )

    def start_event_span(self, event_type: str, operation: str = "publish"):
        if OTEL_AVAILABLE and trace is not None:
            kind = trace.SpanKind.PRODUCER if operation == "publish" else trace.SpanKind.CONSUMER
        else:
            kind = None
        return self.start_span(
            f"event.{operation}.{event_type}",
            kind=kind,
            attributes={
                "event.type": event_type,
                "event.operation": operation,
                "span.type": "event",
            },
        )

    def start_graphql_span(self, operation_type: str, operation_name: str):
        kind = trace.SpanKind.INTERNAL if OTEL_AVAILABLE and trace is not None else None
        return self.start_span(
            f"graphql.{operation_type}.{operation_name}",
            kind=kind,
            attributes={
                "graphql.operation.type": operation_type,
                "graphql.operation.name": operation_name,
                "span.type": "graphql",
            },
        )

    def record_exception(self, span, exception: Exception):
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))

    def set_span_success(self, span):
        span.set_status(Status(StatusCode.OK))

    def add_span_attributes(self, span, attributes: Dict[str, Any]):
        for key, value in attributes.items():
            span.set_attribute(key, value)


tracer = BerylTracer()
