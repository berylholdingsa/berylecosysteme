"""
OpenTelemetry Configuration for Beryl Core API.

Configure traces, metrics, logs export to Jaeger, Zipkin, Prometheus.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging

from src.config.settings import settings


def configure_opentelemetry():
    """Configure OpenTelemetry for traces, metrics, logs."""

    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: "beryl-core-api",
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.SERVICE_NAMESPACE: settings.environment,
    })

    # Tracing
    if settings.tracing_enabled:
        trace.set_tracer_provider(TracerProvider(resource=resource))

        if settings.jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=settings.jaeger_host,
                agent_port=settings.jaeger_port,
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

        if settings.zipkin_endpoint:
            zipkin_exporter = ZipkinExporter(
                endpoint=settings.zipkin_endpoint,
            )
            span_processor = BatchSpanProcessor(zipkin_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

    # Metrics
    if settings.metrics_enabled:
        prometheus_reader = PrometheusMetricReader()
        metric_readers = [prometheus_reader]
        meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
        # Set global meter provider if needed

    # Logs (using standard logging with OTLP if configured)
    # For logs, we can use opentelemetry-distro for auto-instrumentation

    logging.info("OpenTelemetry configured successfully")


# Initialize on import
configure_opentelemetry()