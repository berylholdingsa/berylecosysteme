#!/usr/bin/env python3
"""Architecture audit utility for regulatory readiness scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def contains(path: str, needle: str) -> bool:
    file_path = ROOT / path
    if not file_path.exists():
        return False
    return needle in file_path.read_text(encoding="utf-8")


def run_audit() -> dict:
    checks = [
        (
            "security_governance",
            all(
                exists(path)
                for path in [
                    "security/risk_register.yaml",
                    "security/asset_inventory.yaml",
                    "security/access_control_policy.md",
                    "security/incident_response_plan.md",
                    "security/business_continuity_plan.md",
                    "security/data_classification_policy.md",
                ]
            ),
        ),
        (
            "core_security",
            exists("src/core/security/middleware.py")
            and exists("src/core/security/jwt_rotation.py")
            and exists("src/core/security/crypto.py"),
        ),
        (
            "immutable_audit_chain",
            exists("src/core/audit/service.py")
            and contains("src/core/audit/service.py", "previous_hash")
            and contains("src/core/audit/service.py", "verify_integrity"),
        ),
        (
            "compliance_aml",
            exists("src/compliance/transaction_risk_scorer.py")
            and exists("src/compliance/velocity_checker.py")
            and exists("src/compliance/sanction_list_checker.py")
            and exists("src/compliance/anomaly_detector.py"),
        ),
        (
            "kafka_compliance",
            exists("src/infrastructure/kafka/compliance/schema_registry_validator.py")
            and exists("src/infrastructure/kafka/compliance/event_signature_verifier.py")
            and contains("src/events/bus/kafka_bus.py", "enable_auto_commit=not settings.kafka_manual_commit_only")
            and contains("src/events/bus/kafka_bus.py", "Unsigned financial event rejected"),
        ),
        (
            "observability_metrics",
            contains("src/observability/metrics/prometheus.py", "security_incident_total")
            and contains("src/observability/metrics/prometheus.py", "aml_flagged_total")
            and contains("src/observability/metrics/prometheus.py", "audit_integrity_failures_total")
            and contains("src/observability/metrics/prometheus.py", "signature_validation_failures_total")
            and contains("src/observability/metrics/prometheus.py", "kafka_consumer_lag")
            and contains("src/observability/metrics/prometheus.py", "dlq_events_total"),
        ),
        (
            "chaos_coverage",
            all(
                exists(path)
                for path in [
                    "chaos/corrupt-event-payload.sh",
                    "chaos/invalid-signature.sh",
                    "chaos/simulate-psp-replay.sh",
                    "chaos/flood-2000-tps.sh",
                    "chaos/kill-kafka-broker.sh",
                    "chaos/simulate-db-loss.sh",
                ]
            ),
        ),
        (
            "regulatory_docs",
            all(
                exists(path)
                for path in [
                    "docs/regulatory/architecture.md",
                    "docs/regulatory/data_flow_diagram.md",
                    "docs/regulatory/risk_register.md",
                    "docs/regulatory/incident_handling_process.md",
                    "docs/regulatory/aml_process_description.md",
                    "docs/regulatory/audit_trail_explanation.md",
                    "docs/regulatory/backup_recovery_procedure.md",
                    "docs/regulatory/key_rotation_procedure.md",
                ]
            ),
        ),
        (
            "cicd_regulatory",
            exists(".github/workflows/regulatory-ci.yml")
            and contains(".github/workflows/regulatory-ci.yml", "bandit")
            and contains(".github/workflows/regulatory-ci.yml", "pip-audit")
            and contains(".github/workflows/regulatory-ci.yml", "Chaos Tests"),
        ),
        (
            "structured_logging",
            contains("src/observability/logging/logger.py", "StructuredJSONFormatter")
            and contains("src/observability/logging/logger.py", "json.dumps"),
        ),
    ]

    passed = sum(1 for _, ok in checks if ok)
    score = int((passed / len(checks)) * 100)
    return {
        "score": score,
        "checks": [{"name": name, "passed": ok} for name, ok in checks],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-score", type=int, default=99)
    args = parser.parse_args()

    report = run_audit()
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if args.strict and report["score"] < args.require_score:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
