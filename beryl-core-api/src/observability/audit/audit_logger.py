"""
Audit logging system for compliance and regulatory requirements.

Provides immutable audit trails for sensitive operations in fintech, ESG, and health domains.
"""

import json
import logging
import hashlib
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from pathlib import Path

from src.observability.logging.formatters import AuditFormatter
from src.observability.logging.correlation import get_correlation_id
from src.config.settings import settings


class AuditLogger:
    """
    Specialized logger for audit events with compliance features.
    """

    def __init__(self):
        self.logger = logging.getLogger("beryl-audit")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Add audit-specific handler
        audit_handler = logging.FileHandler(settings.audit_log_file)
        audit_handler.setFormatter(AuditFormatter())
        self.logger.addHandler(audit_handler)

        # Prevent duplicate logs
        self.logger.propagate = False

    def _generate_evidence_hash(self, data: Dict[str, Any]) -> str:
        """Generate cryptographic hash of audit data for integrity."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _log_audit_event(self, audit_event: str, user_id: Optional[str],
                        resource: str, action: str, extra_data: Optional[Dict[str, Any]] = None,
                        compliance_level: str = "STANDARD", ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None):
        """Log audit event with compliance metadata."""

        # Prepare audit data
        audit_data = {
            "audit_event": audit_event,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.now(UTC).isoformat(),
            "compliance_level": compliance_level,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        if extra_data:
            audit_data["extra_data"] = extra_data

        # Generate evidence hash for high-compliance events
        if compliance_level in ["HIGH", "CRITICAL"]:
            audit_data["evidence_hash"] = self._generate_evidence_hash(audit_data)
            audit_data["regulatory_reference"] = "GDPR-2018"  # Default, can be customized
            audit_data["retention_period_days"] = 2555  # 7 years

        # Log the audit event
        self.logger.info(
            f"AUDIT: {audit_event} - {action} on {resource}",
            extra=audit_data
        )

    def log_payment_accessed(self, user_id: str, payment_id: str,
                           action: str = "VIEW", ip_address: Optional[str] = None):
        """Log payment data access."""
        self._log_audit_event(
            audit_event="PAYMENT_ACCESSED",
            user_id=user_id,
            resource=f"payment:{payment_id}",
            action=action,
            compliance_level="HIGH",
            ip_address=ip_address
        )

    def log_wallet_modified(self, user_id: str, wallet_id: str,
                          action: str, amount: float, currency: str = "EUR",
                          ip_address: Optional[str] = None):
        """Log wallet modification."""
        self._log_audit_event(
            audit_event="WALLET_MODIFIED",
            user_id=user_id,
            resource=f"wallet:{wallet_id}",
            action=action,
            extra_data={"amount": amount, "currency": currency},
            compliance_level="CRITICAL",
            ip_address=ip_address
        )

    def log_transaction_executed(self, user_id: str, transaction_id: str,
                               amount: float, currency: str = "EUR",
                               ip_address: Optional[str] = None):
        """Log transaction execution."""
        self._log_audit_event(
            audit_event="TRANSACTION_EXECUTED",
            user_id=user_id,
            resource=f"transaction:{transaction_id}",
            action="EXECUTE",
            extra_data={"amount": amount, "currency": currency},
            compliance_level="CRITICAL",
            ip_address=ip_address
        )

    def log_health_data_accessed(self, user_id: str, data_type: str,
                               action: str = "VIEW", ip_address: Optional[str] = None):
        """Log health data access (GDPR sensitive)."""
        self._log_audit_event(
            audit_event="HEALTH_DATA_ACCESSED",
            user_id=user_id,
            resource=f"health:{data_type}",
            action=action,
            compliance_level="CRITICAL",
            ip_address=ip_address
        )

    def log_esg_score_computed(self, user_id: str, score_type: str,
                             score_value: float, ip_address: Optional[str] = None):
        """Log ESG score computation."""
        self._log_audit_event(
            audit_event="ESG_SCORE_COMPUTED",
            user_id=user_id,
            resource=f"esg:{score_type}",
            action="COMPUTE",
            extra_data={"score_value": score_value},
            compliance_level="HIGH",
            ip_address=ip_address
        )

    def log_pedometer_data_processed(self, user_id: str, steps_count: int,
                                   ip_address: Optional[str] = None):
        """Log pedometer data processing."""
        self._log_audit_event(
            audit_event="PEDOMETER_DATA_PROCESSED",
            user_id=user_id,
            resource="pedometer:data",
            action="PROCESS",
            extra_data={"steps_count": steps_count},
            compliance_level="HIGH",
            ip_address=ip_address
        )

    def log_user_data_exported(self, user_id: str, export_type: str,
                             ip_address: Optional[str] = None):
        """Log user data export (GDPR right of access)."""
        self._log_audit_event(
            audit_event="USER_DATA_EXPORTED",
            user_id=user_id,
            resource=f"export:{export_type}",
            action="EXPORT",
            compliance_level="HIGH",
            ip_address=ip_address
        )

    def log_admin_action(self, admin_user_id: str, action: str,
                        target_resource: str, ip_address: Optional[str] = None):
        """Log administrative action."""
        self._log_audit_event(
            audit_event="ADMIN_ACTION",
            user_id=admin_user_id,
            resource=target_resource,
            action=action,
            compliance_level="HIGH",
            ip_address=ip_address
        )

    def log_security_event(self, event_type: str, user_id: Optional[str],
                          details: Dict[str, Any], ip_address: Optional[str] = None):
        """Log security-related event."""
        self._log_audit_event(
            audit_event=f"SECURITY_{event_type.upper()}",
            user_id=user_id,
            resource="security",
            action="DETECT",
            extra_data=details,
            compliance_level="CRITICAL",
            ip_address=ip_address
        )


# Global audit logger instance
audit_logger = AuditLogger()