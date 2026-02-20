"""Event-driven architecture layer."""
from .base import DomainEvent, DomainEventType
from .bus import get_event_bus, AbstractEventBus
from .registry import initialize_event_system, shutdown_event_system
from .producers import fintech_producer, mobility_producer, esg_producer, social_producer

__all__ = [
    "DomainEvent", "DomainEventType",
    "get_event_bus", "AbstractEventBus",
    "initialize_event_system", "shutdown_event_system",
    "fintech_producer", "mobility_producer", "esg_producer", "social_producer"
]
