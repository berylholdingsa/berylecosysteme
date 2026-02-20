"""Prometheus metrics for GreenOS Outbox relay."""

from __future__ import annotations

from src.observability.metrics.prometheus import Counter, Gauge

greenos_outbox_pending = Gauge(
    "greenos_outbox_pending",
    "Number of GreenOS outbox events pending publication",
)

greenos_outbox_failed_total = Counter(
    "greenos_outbox_failed_total",
    "Total number of GreenOS outbox events marked as failed",
)

greenos_outbox_retry_total = Counter(
    "greenos_outbox_retry_total",
    "Total number of GreenOS outbox publish retries",
)

