"""
Audit event types and definitions for compliance tracking.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class AuditEventType(Enum):
    """Enumeration of all audit event types."""

    # Payment & Financial Events
    PAYMENT_ACCESSED = "PAYMENT_ACCESSED"
    PAYMENT_EXECUTED = "PAYMENT_EXECUTED"
    WALLET_ACCESSED = "WALLET_ACCESSED"
    WALLET_MODIFIED = "WALLET_MODIFIED"
    TRANSACTION_EXECUTED = "TRANSACTION_EXECUTED"
    REFUND_PROCESSED = "REFUND_PROCESSED"

    # Health & ESG Data Events
    HEALTH_DATA_ACCESSED = "HEALTH_DATA_ACCESSED"
    HEALTH_DATA_MODIFIED = "HEALTH_DATA_MODIFIED"
    PEDOMETER_DATA_PROCESSED = "PEDOMETER_DATA_PROCESSED"
    ESG_SCORE_COMPUTED = "ESG_SCORE_COMPUTED"
    ESG_PROFILE_ACCESSED = "ESG_PROFILE_ACCESSED"

    # User Data Events
    USER_DATA_EXPORTED = "USER_DATA_EXPORTED"
    USER_DATA_DELETED = "USER_DATA_DELETED"
    USER_CONSENT_UPDATED = "USER_CONSENT_UPDATED"

    # Social & Content Events
    CONTENT_FLAGGED = "CONTENT_FLAGGED"
    USER_BLOCKED = "USER_BLOCKED"
    MODERATION_ACTION = "MODERATION_ACTION"

    # Administrative Events
    ADMIN_LOGIN = "ADMIN_LOGIN"
    ADMIN_ACTION = "ADMIN_ACTION"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"

    # Security Events
    FAILED_LOGIN_ATTEMPT = "FAILED_LOGIN_ATTEMPT"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    API_KEY_COMPROMISED = "API_KEY_COMPROMISED"

    # System Events
    BACKUP_COMPLETED = "BACKUP_COMPLETED"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"


class ComplianceLevel(Enum):
    """Compliance levels for audit events."""

    STANDARD = "STANDARD"      # Basic logging
    HIGH = "HIGH"             # Requires evidence hash
    CRITICAL = "CRITICAL"     # Requires full regulatory compliance


@dataclass
class AuditEvent:
    """
    Structured audit event definition.
    """

    event_type: AuditEventType
    user_id: Optional[str]
    resource: str
    action: str
    compliance_level: ComplianceLevel
    extra_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    retention_days: int = 2555  # 7 years default

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource": self.resource,
            "action": self.action,
            "compliance_level": self.compliance_level.value,
            "extra_data": self.extra_data,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "retention_days": self.retention_days,
        }


# Predefined audit events for common operations
AUDIT_EVENTS = {
    # Financial operations
    "payment_processed": AuditEvent(
        event_type=AuditEventType.PAYMENT_EXECUTED,
        user_id=None,  # Will be set at runtime
        resource="payment",
        action="PROCESS",
        compliance_level=ComplianceLevel.CRITICAL,
        retention_days=2555
    ),

    "wallet_balance_changed": AuditEvent(
        event_type=AuditEventType.WALLET_MODIFIED,
        user_id=None,
        resource="wallet",
        action="MODIFY",
        compliance_level=ComplianceLevel.CRITICAL,
        retention_days=2555
    ),

    # Health data operations
    "health_data_accessed": AuditEvent(
        event_type=AuditEventType.HEALTH_DATA_ACCESSED,
        user_id=None,
        resource="health",
        action="ACCESS",
        compliance_level=ComplianceLevel.CRITICAL,
        retention_days=2555
    ),

    "pedometer_synced": AuditEvent(
        event_type=AuditEventType.PEDOMETER_DATA_PROCESSED,
        user_id=None,
        resource="pedometer",
        action="SYNC",
        compliance_level=ComplianceLevel.HIGH,
        retention_days=1825  # 5 years
    ),

    # ESG operations
    "esg_score_calculated": AuditEvent(
        event_type=AuditEventType.ESG_SCORE_COMPUTED,
        user_id=None,
        resource="esg",
        action="COMPUTE",
        compliance_level=ComplianceLevel.HIGH,
        retention_days=1825
    ),

    # User operations
    "data_export_requested": AuditEvent(
        event_type=AuditEventType.USER_DATA_EXPORTED,
        user_id=None,
        resource="user_data",
        action="EXPORT",
        compliance_level=ComplianceLevel.HIGH,
        retention_days=2555
    ),

    # Security operations
    "failed_authentication": AuditEvent(
        event_type=AuditEventType.FAILED_LOGIN_ATTEMPT,
        user_id=None,
        resource="authentication",
        action="FAIL",
        compliance_level=ComplianceLevel.HIGH,
        retention_days=365
    ),

    # Administrative operations
    "admin_config_change": AuditEvent(
        event_type=AuditEventType.CONFIGURATION_CHANGED,
        user_id=None,
        resource="configuration",
        action="MODIFY",
        compliance_level=ComplianceLevel.HIGH,
        retention_days=1825
    ),
}


def get_audit_event_template(event_key: str) -> Optional[AuditEvent]:
    """Get predefined audit event template."""
    return AUDIT_EVENTS.get(event_key)


def create_custom_audit_event(event_type: AuditEventType,
                            user_id: Optional[str],
                            resource: str,
                            action: str,
                            compliance_level: ComplianceLevel = ComplianceLevel.STANDARD,
                            **kwargs) -> AuditEvent:
    """Create custom audit event."""
    return AuditEvent(
        event_type=event_type,
        user_id=user_id,
        resource=resource,
        action=action,
        compliance_level=compliance_level,
        extra_data=kwargs.get('extra_data'),
        ip_address=kwargs.get('ip_address'),
        user_agent=kwargs.get('user_agent'),
        retention_days=kwargs.get('retention_days', 2555)
    )