"""
Audit Logger for Zero-Trust Architecture.

Provides comprehensive audit logging for all security events,
access attempts, and sensitive operations in compliance with
regulatory requirements (GDPR, SOX, etc.).
"""

import json
import logging
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import aiofiles
from src.config.settings import settings
from src.events.producers.audit_producer import AuditEventProducer

class AuditLogger:
    """Comprehensive audit logging for Zero-Trust compliance."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audit_producer = AuditEventProducer()

        # Audit log configuration
        self.audit_log_path = Path(settings.audit_log_path or "/var/log/beryl/audit.log")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Sensitive data masking
        self.sensitive_fields = {
            'password', 'token', 'secret', 'key', 'ssn', 'credit_card',
            'bank_account', 'api_key', 'private_key', 'jwt'
        }

        # Compliance levels
        self.compliance_levels = {
            'fintech': 'HIGH',
            'esg': 'HIGH',
            'mobility': 'MEDIUM',
            'social': 'LOW'
        }

    async def log_access_attempt(self, event_data: Dict[str, Any]):
        """
        Log all access attempts (allowed or denied).

        Args:
            event_data: Access attempt details
        """
        event_type = "ACCESS_ATTEMPT"
        severity = "WARNING" if event_data.get('decision') == 'DENIED' else "INFO"

        await self._log_event(event_type, severity, event_data)

        # Send to event bus for real-time monitoring
        await self.audit_producer.publish_access_event(event_data)

    async def log_authentication_event(self, user_id: str, success: bool,
                                     method: str, ip_address: str,
                                     user_agent: str, failure_reason: str = None):
        """Log authentication events."""
        event_data = {
            'user_id': user_id,
            'success': success,
            'method': method,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'failure_reason': failure_reason,
            'timestamp': datetime.utcnow().isoformat()
        }

        event_type = "AUTHENTICATION"
        severity = "ERROR" if not success else "INFO"

        await self._log_event(event_type, severity, event_data)

    async def log_authorization_event(self, user_id: str, resource: str,
                                    action: str, decision: str,
                                    required_permissions: list,
                                    user_permissions: list):
        """Log authorization decisions."""
        event_data = {
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'decision': decision,
            'required_permissions': required_permissions,
            'user_permissions': user_permissions,
            'timestamp': datetime.utcnow().isoformat()
        }

        event_type = "AUTHORIZATION"
        severity = "WARNING" if decision == 'DENIED' else "INFO"

        await self._log_event(event_type, severity, event_data)

    async def log_sensitive_data_access(self, user_id: str, domain: str,
                                      operation: str, record_ids: list,
                                      justification: str = None):
        """Log access to sensitive data (Fintech, ESG)."""
        event_data = {
            'user_id': user_id,
            'domain': domain,
            'operation': operation,
            'record_ids': record_ids,
            'justification': justification,
            'compliance_level': self.compliance_levels.get(domain, 'UNKNOWN'),
            'timestamp': datetime.utcnow().isoformat()
        }

        # Hash sensitive record IDs for privacy
        if record_ids:
            event_data['record_hashes'] = [
                hashlib.sha256(str(rid).encode()).hexdigest()[:16]
                for rid in record_ids
            ]
            del event_data['record_ids']  # Remove actual IDs

        event_type = "SENSITIVE_DATA_ACCESS"
        severity = "WARNING"

        await self._log_event(event_type, severity, event_data)

    async def log_security_incident(self, incident_type: str, severity: str,
                                  description: str, affected_users: list = None,
                                  affected_resources: list = None):
        """Log security incidents."""
        event_data = {
            'incident_type': incident_type,
            'severity': severity,
            'description': description,
            'affected_users': affected_users or [],
            'affected_resources': affected_resources or [],
            'timestamp': datetime.utcnow().isoformat()
        }

        event_type = "SECURITY_INCIDENT"
        await self._log_event(event_type, severity, event_data)

        # Trigger immediate alerts for high-severity incidents
        if severity in ['CRITICAL', 'HIGH']:
            await self._trigger_security_alert(event_data)

    async def log_response(self, event_data: Dict[str, Any]):
        """Log API responses for audit trails."""
        event_type = "API_RESPONSE"
        severity = "ERROR" if event_data.get('status_code', 200) >= 400 else "DEBUG"

        await self._log_event(event_type, severity, event_data)

    async def log_token_event(self, user_id: str, event_type: str,
                            token_id: str = None, ip_address: str = None):
        """Log token-related events (creation, validation, revocation)."""
        event_data = {
            'user_id': user_id,
            'event_type': event_type,
            'token_id': token_id,
            'ip_address': ip_address,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Hash token ID for security
        if token_id:
            event_data['token_hash'] = hashlib.sha256(token_id.encode()).hexdigest()[:16]
            del event_data['token_id']

        event_type = "TOKEN_EVENT"
        severity = "INFO"

        await self._log_event(event_type, severity, event_data)

    async def log_rate_limit_event(self, user_id: str, endpoint: str,
                                 limit: str, window: str):
        """Log rate limiting events."""
        event_data = {
            'user_id': user_id,
            'endpoint': endpoint,
            'limit': limit,
            'window': window,
            'timestamp': datetime.utcnow().isoformat()
        }

        event_type = "RATE_LIMIT"
        severity = "WARNING"

        await self._log_event(event_type, severity, event_data)

    async def _log_event(self, event_type: str, severity: str, event_data: Dict[str, Any]):
        """Internal method to log events to file and event bus."""
        try:
            # Create audit log entry
            log_entry = {
                'event_type': event_type,
                'severity': severity,
                'event_data': self._sanitize_event_data(event_data),
                'log_timestamp': datetime.utcnow().isoformat(),
                'source': 'beryl-core-api'
            }

            # Write to audit log file
            await self._write_to_audit_log(log_entry)

            # Log to application logger
            log_method = getattr(self.logger, severity.lower(), self.logger.info)
            log_method(f"AUDIT: {event_type} - {json.dumps(log_entry, default=str)}")

        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")

    async def _write_to_audit_log(self, log_entry: Dict[str, Any]):
        """Write audit entry to secure log file."""
        try:
            log_line = json.dumps(log_entry, default=str, ensure_ascii=False) + "\n"

            async with aiofiles.open(self.audit_log_path, 'a', encoding='utf-8') as f:
                await f.write(log_line)

            # Rotate log if too large (simple rotation)
            if self.audit_log_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                await self._rotate_audit_log()

        except Exception as e:
            self.logger.error(f"Failed to write to audit log: {e}")

    async def _rotate_audit_log(self):
        """Rotate audit log file."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            rotated_path = self.audit_log_path.with_suffix(f".{timestamp}.log")

            # Rename current log
            self.audit_log_path.rename(rotated_path)

            # Create new log file
            self.audit_log_path.touch()

            self.logger.info(f"Audit log rotated to {rotated_path}")

        except Exception as e:
            self.logger.error(f"Failed to rotate audit log: {e}")

    def _sanitize_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from audit logs."""
        sanitized = {}

        for key, value in event_data.items():
            if key.lower() in self.sensitive_fields:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_event_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_event_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    async def _trigger_security_alert(self, incident_data: Dict[str, Any]):
        """Trigger security alerts for high-severity incidents."""
        try:
            # Send to monitoring system
            alert_data = {
                'alert_type': 'SECURITY_INCIDENT',
                'severity': incident_data['severity'],
                'description': incident_data['description'],
                'timestamp': incident_data['timestamp']
            }

            # TODO: Integrate with alerting system (PagerDuty, OpsGenie, etc.)
            self.logger.critical(f"SECURITY ALERT: {json.dumps(alert_data, default=str)}")

        except Exception as e:
            self.logger.error(f"Failed to trigger security alert: {e}")

    async def query_audit_logs(self, filters: Dict[str, Any],
                             start_date: datetime = None,
                             end_date: datetime = None) -> list:
        """Query audit logs with filters (for auditors only)."""
        # TODO: Implement secure audit log querying
        # This should only be accessible to auditors with proper authorization
        return []

    def get_compliance_report(self, domain: str, start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Generate compliance reports for regulatory requirements."""
        # TODO: Implement compliance reporting
        return {
            'domain': domain,
            'period': f"{start_date.date()} to {end_date.date()}",
            'total_events': 0,
            'security_incidents': 0,
            'access_denials': 0,
            'compliance_status': 'UNKNOWN'
        }