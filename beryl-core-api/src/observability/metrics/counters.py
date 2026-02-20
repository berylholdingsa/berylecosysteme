"""
Custom counters for specific business metrics.
"""

from src.observability.metrics.prometheus import metrics
from src.observability.metrics.prometheus import Counter


class BusinessCounters:
    """
    Specialized counters for business operations.
    """

    def __init__(self):
        # Domain-specific counters
        self.fintech_operations = Counter(
            'beryl_fintech_operations_total',
            'Fintech operations by type',
            ['operation_type', 'currency', 'status']
        )

        self.mobility_operations = Counter(
            'beryl_mobility_operations_total',
            'Mobility operations by type',
            ['operation_type', 'vehicle_type', 'status']
        )

        self.esg_operations = Counter(
            'beryl_esg_operations_total',
            'ESG operations by type',
            ['operation_type', 'data_type', 'status']
        )

        self.social_operations = Counter(
            'beryl_social_operations_total',
            'Social operations by type',
            ['operation_type', 'content_type', 'status']
        )

        # Compliance counters
        self.gdpr_compliance_events = Counter(
            'beryl_gdpr_compliance_events_total',
            'GDPR compliance events',
            ['event_type', 'data_category']
        )

        self.audit_events = Counter(
            'beryl_audit_events_total',
            'Audit events by category',
            ['category', 'severity']
        )

    def increment_fintech_operation(self, operation_type: str,
                                  currency: str = 'EUR',
                                  success: bool = True):
        """Increment fintech operation counter."""
        status = 'success' if success else 'failure'
        self.fintech_operations.labels(
            operation_type=operation_type,
            currency=currency,
            status=status
        ).inc()

    def increment_mobility_operation(self, operation_type: str,
                                   vehicle_type: str = 'unknown',
                                   success: bool = True):
        """Increment mobility operation counter."""
        status = 'success' if success else 'failure'
        self.mobility_operations.labels(
            operation_type=operation_type,
            vehicle_type=vehicle_type,
            status=status
        ).inc()

    def increment_esg_operation(self, operation_type: str,
                              data_type: str = 'health',
                              success: bool = True):
        """Increment ESG operation counter."""
        status = 'success' if success else 'failure'
        self.esg_operations.labels(
            operation_type=operation_type,
            data_type=data_type,
            status=status
        ).inc()

    def increment_social_operation(self, operation_type: str,
                                 content_type: str = 'post',
                                 success: bool = True):
        """Increment social operation counter."""
        status = 'success' if success else 'failure'
        self.social_operations.labels(
            operation_type=operation_type,
            content_type=content_type,
            status=status
        ).inc()

    def increment_gdpr_event(self, event_type: str, data_category: str):
        """Increment GDPR compliance event."""
        self.gdpr_compliance_events.labels(
            event_type=event_type,
            data_category=data_category
        ).inc()

    def increment_audit_event(self, category: str, severity: str = 'info'):
        """Increment audit event counter."""
        self.audit_events.labels(
            category=category,
            severity=severity
        ).inc()


# Global counters instance
counters = BusinessCounters()
