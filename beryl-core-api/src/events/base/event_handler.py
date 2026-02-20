"""
Event handler base classes for event consumers.

All event handlers must inherit from EventHandler.
Handlers must be idempotent and never modify source domain state.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, List, Type
from src.events.base.event import DomainEvent, DomainEventType
from src.observability.logger import logger
import asyncio


class EventHandler(ABC):
    """Base class for all event handlers."""
    
    def __init__(self):
        self.handled_events: List[str] = []
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """
        Handle an event.
        
        Must be idempotent. If handling fails, should log and not raise.
        """
        pass
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """Check if handler can process this event."""
        pass


class FintechEventHandler(EventHandler):
    """Base class for Fintech domain event handlers."""
    
    async def handle(self, event: DomainEvent) -> None:
        """Default Fintech event handling."""
        if event.domain != "fintech":
            return
        
        try:
            logger.info(f"Processing Fintech event: {event.event_type}")
            await self._process_event(event)
            self.handled_events.append(event.event_id)
        except Exception as e:
            logger.error(
                f"Fintech handler error for event {event.event_id}: {str(e)}",
                extra={"event_type": event.event_type}
            )
    
    @abstractmethod
    async def _process_event(self, event: DomainEvent) -> None:
        """Process the event (override in subclasses)."""
        pass


class MobilityEventHandler(EventHandler):
    """Base class for Mobility domain event handlers."""
    
    async def handle(self, event: DomainEvent) -> None:
        """Default Mobility event handling."""
        if event.domain != "mobility":
            return
        
        try:
            logger.info(f"Processing Mobility event: {event.event_type}")
            await self._process_event(event)
            self.handled_events.append(event.event_id)
        except Exception as e:
            logger.error(
                f"Mobility handler error for event {event.event_id}: {str(e)}",
                extra={"event_type": event.event_type}
            )
    
    @abstractmethod
    async def _process_event(self, event: DomainEvent) -> None:
        """Process the event (override in subclasses)."""
        pass


class EsgEventHandler(EventHandler):
    """Base class for ESG domain event handlers."""
    
    async def handle(self, event: DomainEvent) -> None:
        """Default ESG event handling."""
        if event.domain != "esg":
            return
        
        try:
            logger.info(f"Processing ESG event: {event.event_type}")
            await self._process_event(event)
            self.handled_events.append(event.event_id)
        except Exception as e:
            logger.error(
                f"ESG handler error for event {event.event_id}: {str(e)}",
                extra={"event_type": event.event_type}
            )
    
    @abstractmethod
    async def _process_event(self, event: DomainEvent) -> None:
        """Process the event (override in subclasses)."""
        pass


class SocialEventHandler(EventHandler):
    """Base class for Social domain event handlers."""
    
    async def handle(self, event: DomainEvent) -> None:
        """Default Social event handling."""
        if event.domain != "social":
            return
        
        try:
            logger.info(f"Processing Social event: {event.event_type}")
            await self._process_event(event)
            self.handled_events.append(event.event_id)
        except Exception as e:
            logger.error(
                f"Social handler error for event {event.event_id}: {str(e)}",
                extra={"event_type": event.event_type}
            )
    
    @abstractmethod
    async def _process_event(self, event: DomainEvent) -> None:
        """Process the event (override in subclasses)."""
        pass


class EventHandlerRegistry:
    """Registry for event handlers with pub/sub pattern."""
    
    def __init__(self):
        self.handlers: Dict[DomainEventType, List[EventHandler]] = {}
        self.handler_count = 0
    
    def register(
        self,
        event_type: DomainEventType,
        handler: EventHandler
    ) -> None:
        """Register handler for event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        self.handler_count += 1
        logger.info(f"Registered handler for {event_type}: {handler.__class__.__name__}")
    
    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch event to all registered handlers."""
        handlers = self.handlers.get(event.event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers for event type: {event.event_type}")
            return
        
        # Run all handlers concurrently
        tasks = [handler.handle(event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_handlers_for_event(self, event_type: DomainEventType) -> List[EventHandler]:
        """Get all handlers for an event type."""
        return self.handlers.get(event_type, [])
    
    def handler_stats(self) -> Dict[str, Any]:
        """Get statistics about registered handlers."""
        return {
            "total_handlers": self.handler_count,
            "event_types_with_handlers": len(self.handlers),
            "handlers_per_event": {
                str(event_type): len(handlers)
                for event_type, handlers in self.handlers.items()
            }
        }


class EventBus(ABC):
    """Abstract event bus interface."""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all subscribers."""
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        event_type: DomainEventType,
        handler: EventHandler
    ) -> None:
        """Subscribe handler to event type."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the event bus."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus."""
        pass
