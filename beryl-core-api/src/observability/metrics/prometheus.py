"""
Prometheus metrics integration for Beryl Core API.

Provides comprehensive metrics collection and exposure for monitoring,
alerting, and performance analysis.
"""

import time
from typing import Dict, Any, Optional

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
except ModuleNotFoundError:  # pragma: no cover - runtime dependency guard
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class _NoopMetric:
        def labels(self, **kwargs):
            _ = kwargs
            return self

        def inc(self, amount=1):
            _ = amount
            return None

        def observe(self, value):
            _ = value
            return None

        def set(self, value):
            _ = value
            return None

        @property
        def _value(self):  # pylint: disable=invalid-name
            class _Value:
                @staticmethod
                def get():
                    return 0

            return _Value()

    class Counter(_NoopMetric):
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

    class Histogram(_NoopMetric):
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

    class Gauge(_NoopMetric):
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

    class CollectorRegistry:  # pylint: disable=too-few-public-methods
        pass

    class GaugeMetricFamily:  # pylint: disable=too-few-public-methods
        pass

    class CounterMetricFamily:  # pylint: disable=too-few-public-methods
        pass

    def generate_latest(_registry):
        return b""

from src.config.settings import settings


class BerylMetrics:
    """
    Centralized metrics collection for Beryl Core API.
    """

    def __init__(self):
        self.registry = CollectorRegistry()

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            'beryl_http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code', 'domain'],
            registry=self.registry
        )

        self.http_request_duration = Histogram(
            'beryl_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'domain'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )

        # Business Domain Metrics
        self.business_operations_total = Counter(
            'beryl_business_operations_total',
            'Total number of business operations',
            ['domain', 'operation', 'status'],
            registry=self.registry
        )

        self.business_operation_duration = Histogram(
            'beryl_business_operation_duration_seconds',
            'Business operation duration in seconds',
            ['domain', 'operation'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )

        # Event System Metrics
        self.events_published_total = Counter(
            'beryl_events_published_total',
            'Total number of events published',
            ['domain', 'event_type'],
            registry=self.registry
        )

        self.events_consumed_total = Counter(
            'beryl_events_consumed_total',
            'Total number of events consumed',
            ['domain', 'event_type', 'consumer'],
            registry=self.registry
        )

        # Adapter Metrics
        self.adapter_calls_total = Counter(
            'beryl_adapter_calls_total',
            'Total number of adapter calls',
            ['adapter', 'method', 'status'],
            registry=self.registry
        )

        self.adapter_call_duration = Histogram(
            'beryl_adapter_call_duration_seconds',
            'Adapter call duration in seconds',
            ['adapter', 'method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry
        )

        # Error Metrics
        self.errors_total = Counter(
            'beryl_errors_total',
            'Total number of errors',
            ['domain', 'error_type', 'component'],
            registry=self.registry
        )

        # Resource Metrics
        self.active_connections = Gauge(
            'beryl_active_connections',
            'Number of active connections',
            registry=self.registry
        )

        self.memory_usage_bytes = Gauge(
            'beryl_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )

        # Custom Business Metrics
        self.financial_transactions_total = Counter(
            'beryl_financial_transactions_total',
            'Total number of financial transactions',
            ['type', 'status'],
            registry=self.registry
        )

        self.rides_completed_total = Counter(
            'beryl_rides_completed_total',
            'Total number of completed rides',
            ['vehicle_type'],
            registry=self.registry
        )

        self.esg_scores_computed_total = Counter(
            'beryl_esg_scores_computed_total',
            'Total number of ESG scores computed',
            ['score_type'],
            registry=self.registry
        )

        self.social_posts_created_total = Counter(
            'beryl_social_posts_created_total',
            'Total number of social posts created',
            ['post_type'],
            registry=self.registry
        )

        # AOQ Metrics
        self.aoq_decisions_total = Counter(
            'aoq_decisions_total',
            'Total number of AOQ decisions',
            ['decision'],
            registry=self.registry
        )
        self.aoq_approvals_total = Counter(
            'aoq_approvals_total',
            'Total AOQ approved decisions',
            registry=self.registry
        )
        self.aoq_rejections_total = Counter(
            'aoq_rejections_total',
            'Total AOQ rejected decisions',
            registry=self.registry
        )
        self.aoq_latency_seconds = Histogram(
            'aoq_latency_seconds',
            'AOQ decision latency in seconds',
            buckets=[0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
        self.aoq_active_rules = Gauge(
            'aoq_active_rules',
            'Number of active AOQ rules',
            registry=self.registry
        )

        # Bank-grade compliance and security metrics
        self.security_incident_total = Counter(
            "security_incident_total",
            "Total security incidents by reason",
            ["reason"],
            registry=self.registry,
        )
        self.aml_flagged_total = Counter(
            "aml_flagged_total",
            "Total AML flagged transactions",
            ["reason"],
            registry=self.registry,
        )
        self.audit_integrity_failures_total = Counter(
            "audit_integrity_failures_total",
            "Audit chain integrity failures",
            registry=self.registry,
        )
        self.idempotency_rejections_total = Counter(
            "idempotency_rejections_total",
            "Idempotency rejections",
            ["scope"],
            registry=self.registry,
        )
        self.beryl_idempotency_rejection_total = Counter(
            "beryl_idempotency_rejection_total",
            "Idempotency rejection total",
            ["scope"],
            registry=self.registry,
        )
        self.signature_validation_failures_total = Counter(
            "signature_validation_failures_total",
            "Signature validation failures",
            ["reason"],
            registry=self.registry,
        )
        self.kafka_consumer_lag = Gauge(
            "kafka_consumer_lag",
            "Kafka consumer lag by topic and partition",
            ["topic", "partition", "group"],
            registry=self.registry,
        )
        self.dlq_events_total = Counter(
            "dlq_events_total",
            "DLQ events produced by topic",
            ["topic"],
            registry=self.registry,
        )
        self.beryl_fintech_risk_score_avg = Gauge(
            "beryl_fintech_risk_score_avg",
            "Average risk score observed in transaction processing",
            registry=self.registry,
        )
        self.beryl_audit_write_latency_ms = Histogram(
            "beryl_audit_write_latency_ms",
            "Audit write latency in milliseconds",
            buckets=[1, 2, 5, 10, 25, 50, 100, 250, 500, 1000],
            registry=self.registry,
        )
        self.beryl_revenue_total = Counter(
            "beryl_revenue_total",
            "Total revenue captured by source and currency",
            ["source", "currency"],
            registry=self.registry,
        )
        self.beryl_fee_collected_total = Counter(
            "beryl_fee_collected_total",
            "Total fee amount collected by fee type and currency",
            ["fee_type", "currency"],
            registry=self.registry,
        )
        self.beryl_fx_volume_total = Counter(
            "beryl_fx_volume_total",
            "Total FX converted volume by pair",
            ["pair"],
            registry=self.registry,
        )
        self.beryl_fx_margin_total = Counter(
            "beryl_fx_margin_total",
            "Total FX margin captured by pair",
            ["pair"],
            registry=self.registry,
        )
        self.beryl_statement_generated_total = Counter(
            "beryl_statement_generated_total",
            "Total number of certified statements generated",
            ["period"],
            registry=self.registry,
        )
        self.beryl_statement_fee_collected_total = Counter(
            "beryl_statement_fee_collected_total",
            "Total certified statement fee collected",
            ["currency"],
            registry=self.registry,
        )
        self.beryl_statement_verification_total = Counter(
            "beryl_statement_verification_total",
            "Total statement verification attempts by status",
            ["status"],
            registry=self.registry,
        )
        self.beryl_tontine_created_total = Counter(
            "beryl_tontine_created_total",
            "Total number of tontine groups created",
            ["frequency_type"],
            registry=self.registry,
        )
        self.beryl_tontine_contribution_total = Counter(
            "beryl_tontine_contribution_total",
            "Total tontine contribution amount",
            ["currency"],
            registry=self.registry,
        )
        self.beryl_tontine_distribution_total = Counter(
            "beryl_tontine_distribution_total",
            "Total tontine distribution amount",
            ["currency"],
            registry=self.registry,
        )
        self.beryl_tontine_default_total = Counter(
            "beryl_tontine_default_total",
            "Total AOQ/default incidents on tontine groups",
            ["reason"],
            registry=self.registry,
        )
        self.beryl_tontine_unanimous_vote_failures_total = Counter(
            "beryl_tontine_unanimous_vote_failures_total",
            "Total unanimous withdrawal vote failures",
            registry=self.registry,
        )
        self.beryl_tontine_schedule_violation_total = Counter(
            "beryl_tontine_schedule_violation_total",
            "Total schedule lock violations detected",
            registry=self.registry,
        )

    def record_http_request(self, method: str, endpoint: str, status_code: int,
                          duration: float, domain: str = 'unknown'):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            domain=domain
        ).inc()

        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint,
            domain=domain
        ).observe(duration)

    def record_business_operation(self, domain: str, operation: str,
                                duration: float, success: bool = True):
        """Record business operation metrics."""
        status = 'success' if success else 'failure'

        self.business_operations_total.labels(
            domain=domain,
            operation=operation,
            status=status
        ).inc()

        self.business_operation_duration.labels(
            domain=domain,
            operation=operation
        ).observe(duration)

    def record_event_published(self, domain: str, event_type: str):
        """Record event publication."""
        self.events_published_total.labels(
            domain=domain,
            event_type=event_type
        ).inc()

    def record_event_consumed(self, domain: str, event_type: str, consumer: str):
        """Record event consumption."""
        self.events_consumed_total.labels(
            domain=domain,
            event_type=event_type,
            consumer=consumer
        ).inc()

    def record_adapter_call(self, adapter: str, method: str,
                          duration: float, success: bool = True):
        """Record adapter call metrics."""
        status = 'success' if success else 'failure'

        self.adapter_calls_total.labels(
            adapter=adapter,
            method=method,
            status=status
        ).inc()

        self.adapter_call_duration.labels(
            adapter=adapter,
            method=method
        ).observe(duration)

    def record_error(self, domain: str, error_type: str, component: str):
        """Record error metrics."""
        self.errors_total.labels(
            domain=domain,
            error_type=error_type,
            component=component
        ).inc()

    def record_financial_transaction(self, transaction_type: str, success: bool = True):
        """Record financial transaction."""
        status = 'success' if success else 'failure'
        self.financial_transactions_total.labels(
            type=transaction_type,
            status=status
        ).inc()

    def record_ride_completed(self, vehicle_type: str = 'unknown'):
        """Record completed ride."""
        self.rides_completed_total.labels(vehicle_type=vehicle_type).inc()

    def record_esg_score_computed(self, score_type: str = 'general'):
        """Record ESG score computation."""
        self.esg_scores_computed_total.labels(score_type=score_type).inc()

    def record_social_post_created(self, post_type: str = 'text'):
        """Record social post creation."""
        self.social_posts_created_total.labels(post_type=post_type).inc()

    def record_aoq_decision(self, decision: str, latency_seconds: float, active_rules: int):
        """Record AOQ-specific decision metrics."""
        normalized = decision.upper()
        self.aoq_decisions_total.labels(decision=normalized).inc()
        if normalized == "APPROVE":
            self.aoq_approvals_total.inc()
        elif normalized == "REJECT":
            self.aoq_rejections_total.inc()
        self.aoq_latency_seconds.observe(latency_seconds)
        self.aoq_active_rules.set(active_rules)

    def record_security_incident(self, reason: str) -> None:
        self.security_incident_total.labels(reason=reason).inc()

    def record_aml_flag(self, reason: str) -> None:
        self.aml_flagged_total.labels(reason=reason).inc()

    def record_audit_integrity_failure(self, count: int = 1) -> None:
        self.audit_integrity_failures_total.inc(count)

    def record_idempotency_rejection(self, scope: str = "fintech") -> None:
        self.idempotency_rejections_total.labels(scope=scope).inc()
        self.beryl_idempotency_rejection_total.labels(scope=scope).inc()

    def record_signature_failure(self, reason: str) -> None:
        self.signature_validation_failures_total.labels(reason=reason).inc()

    def set_kafka_consumer_lag(self, *, topic: str, partition: int, group: str, lag: int) -> None:
        self.kafka_consumer_lag.labels(topic=topic, partition=str(partition), group=group).set(max(0, lag))

    def record_dlq_event(self, topic: str) -> None:
        self.dlq_events_total.labels(topic=topic).inc()

    def observe_fintech_risk_score(self, score: float) -> None:
        current = self.beryl_fintech_risk_score_avg._value.get()  # pylint: disable=protected-access
        if current == 0:
            self.beryl_fintech_risk_score_avg.set(score)
            return
        self.beryl_fintech_risk_score_avg.set((current + score) / 2)

    def record_audit_write_latency(self, latency_ms: float) -> None:
        self.beryl_audit_write_latency_ms.observe(max(0.0, latency_ms))

    def record_revenue_total(self, *, source: str, currency: str, amount: float) -> None:
        self.beryl_revenue_total.labels(source=source, currency=currency).inc(max(0.0, amount))

    def record_fee_collected(self, *, fee_type: str, currency: str, amount: float) -> None:
        self.beryl_fee_collected_total.labels(fee_type=fee_type, currency=currency).inc(max(0.0, amount))

    def record_fx_volume(self, *, pair: str, amount: float) -> None:
        self.beryl_fx_volume_total.labels(pair=pair).inc(max(0.0, amount))

    def record_fx_margin(self, *, pair: str, amount: float) -> None:
        self.beryl_fx_margin_total.labels(pair=pair).inc(max(0.0, amount))

    def record_statement_generated(self, *, period: str) -> None:
        self.beryl_statement_generated_total.labels(period=period).inc()

    def record_statement_fee_collected(self, *, currency: str, amount: float) -> None:
        self.beryl_statement_fee_collected_total.labels(currency=currency).inc(max(0.0, amount))

    def record_statement_verification(self, *, status: str) -> None:
        self.beryl_statement_verification_total.labels(status=status).inc()

    def record_tontine_created(self, *, frequency_type: str) -> None:
        self.beryl_tontine_created_total.labels(frequency_type=frequency_type).inc()

    def record_tontine_contribution(self, *, amount: float, currency: str) -> None:
        self.beryl_tontine_contribution_total.labels(currency=currency).inc(max(0.0, amount))

    def record_tontine_distribution(self, *, amount: float, currency: str) -> None:
        self.beryl_tontine_distribution_total.labels(currency=currency).inc(max(0.0, amount))

    def record_tontine_default(self, *, reason: str) -> None:
        self.beryl_tontine_default_total.labels(reason=reason).inc()

    def record_tontine_unanimous_vote_failure(self) -> None:
        self.beryl_tontine_unanimous_vote_failures_total.inc()

    def record_tontine_schedule_violation(self) -> None:
        self.beryl_tontine_schedule_violation_total.inc()

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        return generate_latest(self.registry).decode('utf-8')

    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary for custom processing."""
        # This would require parsing the Prometheus output
        # For now, return basic info
        return {
            "registry_info": str(self.registry),
            "metrics_endpoint": "/metrics"
        }


# Global metrics instance
metrics = BerylMetrics()
