#!/usr/bin/env python3
"""Bank partner audit simulation for beryl-core-api."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckResult:
    name: str
    passed: bool
    weight: int
    details: dict[str, Any]


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def _contains(path: str, needle: str) -> bool:
    file_path = ROOT / path
    if not file_path.exists():
        return False
    return needle in file_path.read_text(encoding="utf-8")


def _run_command(command: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "duration_ms": duration_ms,
        "stdout_tail": completed.stdout.strip().splitlines()[-20:],
        "stderr_tail": completed.stderr.strip().splitlines()[-20:],
    }


def _pytest_command(target: str) -> list[str]:
    if shutil.which("poetry") and (ROOT / "pyproject.toml").exists():
        return ["poetry", "run", "pytest", "-q", target]
    return ["python3", "-m", "pytest", "-q", target]


def check_policies() -> CheckResult:
    required = [
        "infra/vault-policy.hcl",
        "docs/audit_simulation/politique_gestion_cles.md",
        "docs/audit_simulation/politique_separation_acces.md",
        "security/access_control_policy.md",
        "docs/regulatory/key_rotation_procedure.md",
    ]
    missing = [path for path in required if not _exists(path)]
    passed = len(missing) == 0
    return CheckResult(
        name="policies_existence",
        passed=passed,
        weight=20,
        details={"required": required, "missing": missing},
    )


def check_key_rotation_active() -> CheckResult:
    script_ok = _exists("infra/key-rotation-cron.sh") and os.access(ROOT / "infra/key-rotation-cron.sh", os.X_OK)
    config_ok = _contains("infra/key-rotation-cron.sh", "ROTATION_INTERVAL_DAYS") and _contains(
        "infra/key-rotation-cron.sh", "90"
    )

    env = os.environ.copy()
    env.update(
        {
            "SIMULATE": "true",
            "FORCE_ROTATE": "true",
            "KEY_ROTATION_STATE_FILE": "/tmp/beryl-bank-audit-rotation-state.json",
            "MOCK_SECRETS_FILE": "/tmp/beryl-bank-audit-mock-secrets.json",
        }
    )
    cmd_result = _run_command(["bash", "infra/key-rotation-cron.sh"], env=env)
    passed = script_ok and config_ok and cmd_result["exit_code"] == 0

    return CheckResult(
        name="key_rotation_active",
        passed=passed,
        weight=20,
        details={
            "script_ok": script_ok,
            "config_ok": config_ok,
            "execution": cmd_result,
        },
    )


def check_alerting_active() -> CheckResult:
    required_alerts = [
        "KafkaConsumerLagCritical",
        "DLQEventCritical",
        "AuditIntegrityFailure",
        "AMLSpikeAnomaly",
        "SignatureFailureAnomaly",
        "PSPReplayDetectionAnomaly",
    ]
    alerts_file = "monitoring/alerts/regulatory-alerts.yml"
    infra_rules_file = "infra/prometheus-alert-rules.yml"
    alertmanager_file = "infra/alertmanager.yml"

    alerts_in_monitoring = [name for name in required_alerts if _contains(alerts_file, name)]
    alerts_in_infra = [name for name in required_alerts if _contains(infra_rules_file, name)]
    webhook_configured = _contains(alertmanager_file, "mock-alert-webhook")

    passed = (
        len(alerts_in_monitoring) == len(required_alerts)
        and len(alerts_in_infra) == len(required_alerts)
        and webhook_configured
    )

    return CheckResult(
        name="alerting_active",
        passed=passed,
        weight=20,
        details={
            "required_alerts": required_alerts,
            "alerts_in_monitoring": alerts_in_monitoring,
            "alerts_in_infra": alerts_in_infra,
            "webhook_configured": webhook_configured,
        },
    )


def check_staging_operational() -> CheckResult:
    required_assets = [
        "staging/seed_data_anonymized.json",
        "staging/simulated_transactions.json",
        "staging/aml_cases_positifs_negatifs.json",
        "staging/psp_replay_scenarios.json",
        "staging/fraud_test_scenarios.json",
        "staging/run_staging_compliance_suite.sh",
    ]
    missing = [path for path in required_assets if not _exists(path)]
    executable = os.access(ROOT / "staging/run_staging_compliance_suite.sh", os.X_OK)

    env = os.environ.copy()
    env.update(
        {
            "SUITE_MODE": "simulation",
            "REPORT_PATH": str(ROOT / "staging/reports/staging_compliance_report.json"),
        }
    )
    cmd_result = _run_command(["bash", "staging/run_staging_compliance_suite.sh"], env=env)

    report_path = ROOT / "staging/reports/staging_compliance_report.json"
    report_score = None
    report_status = None
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            report_score = int(data.get("score", 0))
            report_status = data.get("overall_status")
        except Exception:
            report_score = None
            report_status = "invalid"

    passed = (
        len(missing) == 0
        and executable
        and cmd_result["exit_code"] == 0
        and report_status == "passed"
        and report_score == 100
    )

    return CheckResult(
        name="staging_operational",
        passed=passed,
        weight=20,
        details={
            "missing": missing,
            "executable": executable,
            "execution": cmd_result,
            "report_status": report_status,
            "report_score": report_score,
        },
    )


def check_audit_chain_integrity() -> CheckResult:
    test_result = _run_command(_pytest_command("tests/regulatory/test_audit_chain_integrity.py"))
    service_ok = _exists("src/core/audit/service.py") and _contains("src/core/audit/service.py", "verify_integrity")
    passed = test_result["exit_code"] == 0 and service_ok

    return CheckResult(
        name="audit_chain_integrity",
        passed=passed,
        weight=20,
        details={
            "service_ok": service_ok,
            "execution": test_result,
        },
    )


def run_simulation() -> dict[str, Any]:
    checks = [
        check_policies(),
        check_key_rotation_active(),
        check_alerting_active(),
        check_staging_operational(),
        check_audit_chain_integrity(),
    ]

    total_weight = sum(item.weight for item in checks)
    passed_weight = sum(item.weight for item in checks if item.passed)
    score = int((passed_weight / total_weight) * 100) if total_weight else 0

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "simulator": "BankAuditSimulator",
        "total_weight": total_weight,
        "passed_weight": passed_weight,
        "score": score,
        "bank_compliance": "PASS" if score == 100 else "FAIL",
        "checks": [
            {
                "name": item.name,
                "passed": item.passed,
                "weight": item.weight,
                "details": item.details,
            }
            for item in checks
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs/audit_simulation/bank_audit_report.json"),
        help="Output report path",
    )
    parser.add_argument("--strict", action="store_true", help="Fail if score is below required score")
    parser.add_argument("--require-score", type=int, default=100)
    args = parser.parse_args()

    report = run_simulation()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(json.dumps({"event": "bank_audit_simulation", "score": report["score"], "output": str(output_path)}))

    if args.strict and report["score"] < args.require_score:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
