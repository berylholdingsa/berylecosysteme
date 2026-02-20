"""Prometheus metrics for IAESG scoring outcomes."""

from __future__ import annotations

from src.observability.metrics.prometheus import Counter

greenos_iaesg_scored_total = Counter(
    "greenos_iaesg_scored_total",
    "Total number of IAESG scoring evaluations",
)

greenos_iaesg_anomalies_total = Counter(
    "greenos_iaesg_anomalies_total",
    "Total number of IAESG anomalies detected",
    ["flag"],
)

greenos_aoq_review_total = Counter(
    "greenos_aoq_review_total",
    "Total AOQ decisions produced by IAESG",
    ["status"],
)


def record_iaesg_evaluation(*, anomaly_flags: list[str], aoq_status: str) -> None:
    """Emit IAESG metrics for one completed scoring cycle."""
    greenos_iaesg_scored_total.inc()
    for flag in sorted({str(flag) for flag in anomaly_flags}):
        greenos_iaesg_anomalies_total.labels(flag=flag).inc()
    greenos_aoq_review_total.labels(status=str(aoq_status)).inc()
