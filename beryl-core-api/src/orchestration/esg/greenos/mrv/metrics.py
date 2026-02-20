"""Prometheus metrics for GreenOS MRV exports."""

from __future__ import annotations

from src.observability.metrics.prometheus import Counter, Gauge

greenos_mrv_exports_total = Counter(
    "greenos_mrv_exports_total",
    "Total number of GreenOS MRV exports generated",
)

greenos_mrv_verification_failures_total = Counter(
    "greenos_mrv_verification_failures_total",
    "Total number of failed GreenOS MRV verifications",
)

greenos_mrv_methodology_version_active = Gauge(
    "greenos_mrv_methodology_version_active",
    "Active GreenOS MRV methodology version marker (labels carry active version)",
    ["methodology_version"],
)

greenos_mrv_methodology_mismatch_total = Counter(
    "greenos_mrv_methodology_mismatch_total",
    "Total number of MRV export methodology/hash mismatches",
)
