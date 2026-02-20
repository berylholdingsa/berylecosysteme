"""Base event classes."""
from .event import DomainEvent, DomainEventType
from .event_handler import EventHandler, EventBus
__all__ = ["DomainEvent", "DomainEventType", "EventHandler", "EventBus"]
