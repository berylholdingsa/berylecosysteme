"""AOQ bridge status mapping for IAESG outcomes."""

from __future__ import annotations

AOQ_STATUS_PASS = "PASS"
AOQ_STATUS_REVIEW = "REVIEW"
AOQ_STATUS_REJECT = "REJECT"

_CRITICAL_FLAGS = {"CRYPTO_INTEGRITY_FAILURE", "METHODOLOGY_INCONSISTENCE"}


def evaluate_aoq(confidence_score: int, anomaly_flags: list[str]) -> str:
    """Map IAESG score/anomalies to AOQ status."""
    normalized_flags = {str(flag).upper() for flag in anomaly_flags}
    if confidence_score < 50 or _CRITICAL_FLAGS.intersection(normalized_flags):
        return AOQ_STATUS_REJECT
    if 50 <= confidence_score <= 80:
        return AOQ_STATUS_REVIEW
    return AOQ_STATUS_PASS
