"""
Observability package initialization.

This module provides the public API for the observability system.
"""

from .logging.logger import logger
from .logging.correlation import (
    get_correlation_id, set_correlation_id,
    get_request_id, set_request_id,
    get_user_id, set_user_id,
    get_domain, set_domain
)
from .metrics.prometheus import metrics
from .metrics.counters import counters
from .metrics.histograms import histograms
from .tracing.tracer import tracer
from .audit.audit_logger import audit_logger
from .audit.audit_events import AuditEventType, ComplianceLevel, get_audit_event_template
from .observability_bootstrap import observability, init_observability, get_observability_status

__all__ = [
    # Logging
    "logger",
    "get_correlation_id", "set_correlation_id",
    "get_request_id", "set_request_id",
    "get_user_id", "set_user_id",
    "get_domain", "set_domain",

    # Metrics
    "metrics",
    "counters",
    "histograms",

    # Tracing
    "tracer",

    # Audit
    "audit_logger",
    "AuditEventType",
    "ComplianceLevel",
    "get_audit_event_template",

    # Bootstrap
    "observability",
    "init_observability",
    "get_observability_status",
]