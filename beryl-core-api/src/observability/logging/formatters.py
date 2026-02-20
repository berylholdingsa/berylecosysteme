"""
Custom formatters for specialized logging needs.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class AuditFormatter(logging.Formatter):
    """
    Specialized formatter for audit logs with compliance fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format audit log entry with compliance fields."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "AUDIT",
            "service": "beryl-core-api",
            "audit_event": getattr(record, 'audit_event', 'UNKNOWN'),
            "user_id": getattr(record, 'user_id', None),
            "resource": getattr(record, 'resource', None),
            "action": getattr(record, 'action', None),
            "ip_address": getattr(record, 'ip_address', None),
            "user_agent": getattr(record, 'user_agent', None),
            "correlation_id": getattr(record, 'correlation_id', None),
            "message": record.getMessage(),
            "compliance_level": getattr(record, 'compliance_level', 'STANDARD'),
        }

        # Add evidence fields for high-compliance events
        if getattr(record, 'compliance_level', 'STANDARD') in ['HIGH', 'CRITICAL']:
            log_entry.update({
                "evidence_hash": getattr(record, 'evidence_hash', None),
                "regulatory_reference": getattr(record, 'regulatory_reference', None),
                "retention_period_days": getattr(record, 'retention_period_days', 2555),  # 7 years
            })

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class MetricsFormatter(logging.Formatter):
    """
    Formatter for metrics logs that can be parsed by monitoring systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format metrics log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "METRICS",
            "service": "beryl-core-api",
            "metric_name": getattr(record, 'metric_name', 'unknown'),
            "metric_value": getattr(record, 'metric_value', 0),
            "metric_type": getattr(record, 'metric_type', 'counter'),
            "labels": getattr(record, 'labels', {}),
            "message": record.getMessage(),
        }

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class PerformanceFormatter(logging.Formatter):
    """
    Formatter for performance monitoring logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format performance log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "PERFORMANCE",
            "service": "beryl-core-api",
            "operation": getattr(record, 'operation', 'unknown'),
            "duration_ms": getattr(record, 'duration_ms', 0),
            "memory_mb": getattr(record, 'memory_mb', 0),
            "cpu_percent": getattr(record, 'cpu_percent', 0),
            "correlation_id": getattr(record, 'correlation_id', None),
            "message": record.getMessage(),
        }

        return json.dumps(log_entry, default=str, ensure_ascii=False)