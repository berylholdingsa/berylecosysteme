"""Unit tests for AOQ Prometheus metrics."""

from src.observability.metrics.prometheus import BerylMetrics


def test_aoq_metrics_are_recorded_and_exposed():
    local_metrics = BerylMetrics()
    local_metrics.record_aoq_decision(decision="APPROVE", latency_seconds=0.123, active_rules=2)
    local_metrics.record_aoq_decision(decision="REJECT", latency_seconds=0.456, active_rules=1)

    output = local_metrics.get_metrics()
    assert "aoq_decisions_total" in output
    assert "aoq_approvals_total" in output
    assert "aoq_rejections_total" in output
    assert "aoq_latency_seconds" in output
    assert "aoq_active_rules" in output
