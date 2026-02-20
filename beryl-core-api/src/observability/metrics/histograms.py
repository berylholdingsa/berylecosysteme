"""
Custom histograms for performance monitoring.
"""

from src.observability.metrics.prometheus import metrics
from src.observability.metrics.prometheus import Histogram


class PerformanceHistograms:
    """
    Specialized histograms for performance monitoring.
    """

    def __init__(self):
        # Domain-specific performance histograms
        self.fintech_operation_duration = Histogram(
            'beryl_fintech_operation_duration_seconds',
            'Fintech operation duration',
            ['operation_type', 'currency'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        self.mobility_operation_duration = Histogram(
            'beryl_mobility_operation_duration_seconds',
            'Mobility operation duration',
            ['operation_type', 'vehicle_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        self.esg_operation_duration = Histogram(
            'beryl_esg_operation_duration_seconds',
            'ESG operation duration',
            ['operation_type', 'data_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        self.social_operation_duration = Histogram(
            'beryl_social_operation_duration_seconds',
            'Social operation duration',
            ['operation_type', 'content_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        # External service call histograms
        self.external_api_duration = Histogram(
            'beryl_external_api_duration_seconds',
            'External API call duration',
            ['service', 'method', 'status'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        self.database_query_duration = Histogram(
            'beryl_database_query_duration_seconds',
            'Database query duration',
            ['operation', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )

        # Event processing histograms
        self.event_processing_duration = Histogram(
            'beryl_event_processing_duration_seconds',
            'Event processing duration',
            ['event_type', 'processor'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
        )

        # GraphQL specific histograms
        self.graphql_query_duration = Histogram(
            'beryl_graphql_query_duration_seconds',
            'GraphQL query duration',
            ['operation_name', 'complexity'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )

        self.graphql_mutation_duration = Histogram(
            'beryl_graphql_mutation_duration_seconds',
            'GraphQL mutation duration',
            ['mutation_name', 'complexity'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )

    def observe_fintech_operation(self, operation_type: str,
                                duration: float, currency: str = 'EUR'):
        """Observe fintech operation duration."""
        self.fintech_operation_duration.labels(
            operation_type=operation_type,
            currency=currency
        ).observe(duration)

    def observe_mobility_operation(self, operation_type: str,
                                 duration: float, vehicle_type: str = 'unknown'):
        """Observe mobility operation duration."""
        self.mobility_operation_duration.labels(
            operation_type=operation_type,
            vehicle_type=vehicle_type
        ).observe(duration)

    def observe_esg_operation(self, operation_type: str,
                            duration: float, data_type: str = 'health'):
        """Observe ESG operation duration."""
        self.esg_operation_duration.labels(
            operation_type=operation_type,
            data_type=data_type
        ).observe(duration)

    def observe_social_operation(self, operation_type: str,
                               duration: float, content_type: str = 'post'):
        """Observe social operation duration."""
        self.social_operation_duration.labels(
            operation_type=operation_type,
            content_type=content_type
        ).observe(duration)

    def observe_external_api_call(self, service: str, method: str,
                                duration: float, success: bool = True):
        """Observe external API call duration."""
        status = 'success' if success else 'failure'
        self.external_api_duration.labels(
            service=service,
            method=method,
            status=status
        ).observe(duration)

    def observe_database_query(self, operation: str, table: str, duration: float):
        """Observe database query duration."""
        self.database_query_duration.labels(
            operation=operation,
            table=table
        ).observe(duration)

    def observe_event_processing(self, event_type: str, processor: str, duration: float):
        """Observe event processing duration."""
        self.event_processing_duration.labels(
            event_type=event_type,
            processor=processor
        ).observe(duration)

    def observe_graphql_query(self, operation_name: str, duration: float, complexity: int = 1):
        """Observe GraphQL query duration."""
        self.graphql_query_duration.labels(
            operation_name=operation_name,
            complexity=str(complexity)
        ).observe(duration)

    def observe_graphql_mutation(self, mutation_name: str, duration: float, complexity: int = 1):
        """Observe GraphQL mutation duration."""
        self.graphql_mutation_duration.labels(
            mutation_name=mutation_name,
            complexity=str(complexity)
        ).observe(duration)


# Global histograms instance
histograms = PerformanceHistograms()
