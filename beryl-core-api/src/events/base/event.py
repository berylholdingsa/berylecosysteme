"""
Base Event model for event-driven architecture.

All events in the system must inherit from DomainEvent.
Events are immutable, serializable, and carry domain semantics.
"""

from typing import Dict, Any, Optional, Mapping
from types import MappingProxyType
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class DomainEventType(str, Enum):
    """Enumeration of all domain event types."""
    # Fintech events
    WALLET_CREDITED = "fintech.wallet.credited"
    TRANSACTION_COMPLETED = "fintech.transaction.completed"
    PAYMENT_FAILED = "fintech.payment.failed"
    WALLET_CREATED = "fintech.wallet.created"
    
    # Mobility events
    RIDE_COMPLETED = "mobility.ride.completed"
    FLEET_OPTIMIZED = "mobility.fleet.optimized"
    DEMAND_PREDICTED = "mobility.demand.predicted"
    VEHICLE_STATUS_UPDATED = "mobility.vehicle.status.updated"
    
    # ESG events
    ESG_SCORE_COMPUTED = "esg.score.computed"
    PEDOMETER_UPDATED = "esg.pedometer.updated"
    SUSTAINABILITY_REPORT_GENERATED = "esg.report.generated"
    HEALTH_PROFILE_UPDATED = "esg.health.profile.updated"
    
    # Social events
    POST_CREATED = "social.post.created"
    FEED_GENERATED = "social.feed.generated"
    CONTENT_FLAGGED = "social.content.flagged"
    USER_REGISTERED = "social.user.registered"
    CONNECTION_SUGGESTED = "social.connection.suggested"
    
    # Cross-domain events
    USER_JOINED = "system.user.joined"
    USER_DELETED = "system.user.deleted"
    ERROR_OCCURRED = "system.error.occurred"


class DomainEvent(BaseModel):
    """Base class for all domain events."""
    
    model_config = ConfigDict(frozen=True)
    
    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique event identifier"
    )
    event_type: DomainEventType = Field(
        ...,
        description="Type of domain event"
    )
    domain: str = Field(
        ...,
        description="Domain that generated the event (fintech, mobility, esg, social)"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event creation timestamp"
    )
    payload: Mapping[str, Any] = Field(
        ...,
        description="Event-specific data"
    )
    
    @field_validator('payload', mode='after')
    @classmethod
    def make_payload_immutable(cls, v):
        if isinstance(v, dict):
            return MappingProxyType(v)
        return v
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (correlation_id, user_id, etc.)"
    )
    version: int = Field(
        default=1,
        description="Event schema version"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        data = self.model_dump(mode='json', by_alias=True, exclude={'payload'})
        data['payload'] = dict(self.payload) if isinstance(self.payload, MappingProxyType) else self.payload
        return data
    
    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from metadata."""
        return self.metadata.get("correlation_id")
    
    def get_user_id(self) -> Optional[str]:
        """Get user ID from metadata."""
        return self.metadata.get("user_id")
    
    def with_correlation_id(self, correlation_id: str) -> "DomainEvent":
        """Create a copy with correlation ID (since events are immutable)."""
        data = self.dict()
        data["metadata"]["correlation_id"] = correlation_id
        return DomainEvent(**data)


# Concrete event implementations

class WalletCreditedEvent(DomainEvent):
    """Event emitted when wallet is credited."""
    event_type: DomainEventType = DomainEventType.WALLET_CREDITED
    domain: str = "fintech"


class TransactionCompletedEvent(DomainEvent):
    """Event emitted when transaction completes."""
    event_type: DomainEventType = DomainEventType.TRANSACTION_COMPLETED
    domain: str = "fintech"


class PaymentFailedEvent(DomainEvent):
    """Event emitted when payment fails."""
    event_type: DomainEventType = DomainEventType.PAYMENT_FAILED
    domain: str = "fintech"


class RideCompletedEvent(DomainEvent):
    """Event emitted when ride completes."""
    event_type: DomainEventType = DomainEventType.RIDE_COMPLETED
    domain: str = "mobility"


class FleetOptimizedEvent(DomainEvent):
    """Event emitted when fleet is optimized."""
    event_type: DomainEventType = DomainEventType.FLEET_OPTIMIZED
    domain: str = "mobility"


class DemandPredictedEvent(DomainEvent):
    """Event emitted when demand is predicted."""
    event_type: DomainEventType = DomainEventType.DEMAND_PREDICTED
    domain: str = "mobility"


class EsgScoreComputedEvent(DomainEvent):
    """Event emitted when ESG score is computed."""
    event_type: DomainEventType = DomainEventType.ESG_SCORE_COMPUTED
    domain: str = "esg"


class PedometerUpdatedEvent(DomainEvent):
    """Event emitted when pedometer data is updated."""
    event_type: DomainEventType = DomainEventType.PEDOMETER_UPDATED
    domain: str = "esg"


class PostCreatedEvent(DomainEvent):
    """Event emitted when post is created."""
    event_type: DomainEventType = DomainEventType.POST_CREATED
    domain: str = "social"


class FeedGeneratedEvent(DomainEvent):
    """Event emitted when feed is generated."""
    event_type: DomainEventType = DomainEventType.FEED_GENERATED
    domain: str = "social"


class ContentFlaggedEvent(DomainEvent):
    """Event emitted when content is flagged."""
    event_type: DomainEventType = DomainEventType.CONTENT_FLAGGED
    domain: str = "social"


class UserRegisteredEvent(DomainEvent):
    """Event emitted when user registers."""
    event_type: DomainEventType = DomainEventType.USER_REGISTERED
    domain: str = "system"
