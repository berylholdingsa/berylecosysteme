"""
Abstract Event Bus interface.

Broker-agnostic abstraction for publish/subscribe pattern.
Implementations: Kafka, RabbitMQ, Redis (mock for dev).
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from src.events.base.event import DomainEvent, DomainEventType
from src.events.base.event_handler import EventHandler, EventBus
from src.observability.logger import logger


class AbstractEventBus(EventBus):
    """Abstract base for all event bus implementations."""
    
    def __init__(self, broker_type: str = "mock"):
        self.broker_type = broker_type
        self.handlers: Dict[DomainEventType, List[EventHandler]] = {}
        self.is_running = False
        self.event_count = 0
        self.error_count = 0
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish event (template method)."""
        try:
            self.event_count += 1
            
            logger.info(
                f"Publishing event: {event.event_type}",
                extra={
                    "event_id": event.event_id,
                    "domain": event.domain,
                    "broker": self.broker_type
                }
            )
            
            # Serialize event
            event_data = event.to_dict()
            await self._publish_impl(event.event_type, event_data)
            
        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Failed to publish event: {str(e)}",
                extra={"event_id": event.event_id}
            )
            raise

    async def publish_raw(self, *, topic: str, key: str, payload: Dict[str, Any]) -> None:
        """Publish a broker-native payload not bound to DomainEvent enum."""
        try:
            await self._publish_raw_impl(topic=topic, key=key, payload=payload)
        except Exception:
            self.error_count += 1
            raise
    
    @abstractmethod
    async def _publish_impl(
        self,
        event_type: DomainEventType,
        event_data: Dict[str, Any]
    ) -> None:
        """Implementation-specific publishing (override in subclasses)."""
        pass

    @abstractmethod
    async def _publish_raw_impl(self, *, topic: str, key: str, payload: Dict[str, Any]) -> None:
        """Implementation-specific raw topic publish path."""
        pass
    
    async def subscribe(
        self,
        event_type: DomainEventType,
        handler: EventHandler
    ) -> None:
        """Subscribe handler to event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(
            f"Subscribed handler for {event_type}",
            extra={"handler": handler.__class__.__name__}
        )
    
    async def start(self) -> None:
        """Start the event bus."""
        self.is_running = True
        logger.info(f"Event bus started: {self.broker_type}")
        await self._start_impl()
    
    @abstractmethod
    async def _start_impl(self) -> None:
        """Implementation-specific startup."""
        pass
    
    async def stop(self) -> None:
        """Stop the event bus."""
        self.is_running = False
        logger.info(f"Event bus stopped: {self.broker_type}")
        await self._stop_impl()
    
    @abstractmethod
    async def _stop_impl(self) -> None:
        """Implementation-specific shutdown."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "broker_type": self.broker_type,
            "is_running": self.is_running,
            "events_published": self.event_count,
            "errors": self.error_count,
            "subscriptions": {
                str(event_type): len(handlers)
                for event_type, handlers in self.handlers.items()
            }
        }


class MockEventBus(AbstractEventBus):
    """In-memory mock event bus for development/testing."""
    
    def __init__(self):
        super().__init__(broker_type="mock")
        self.published_events: List[DomainEvent] = []
    
    async def _publish_impl(
        self,
        event_type: DomainEventType,
        event_data: Dict[str, Any]
    ) -> None:
        """Store event in memory and dispatch to handlers."""
        # Store event
        event = DomainEvent(**event_data)
        self.published_events.append(event)
        
        # Dispatch to handlers
        handlers = self.handlers.get(event_type, [])
        tasks = [handler.handle(event) for handler in handlers]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _publish_raw_impl(self, *, topic: str, key: str, payload: Dict[str, Any]) -> None:
        event = DomainEvent(
            event_type=DomainEventType.ERROR_OCCURRED,
            domain="system",
            payload={"topic": topic, "key": key, "payload": payload},
            metadata={"transport": "mock"},
        )
        self.published_events.append(event)
    
    async def _start_impl(self) -> None:
        """No-op for mock bus."""
        pass
    
    async def _stop_impl(self) -> None:
        """No-op for mock bus."""
        pass
    
    def get_published_events(self) -> List[DomainEvent]:
        """Get all published events (for testing)."""
        return self.published_events.copy()
    
    def clear_events(self) -> None:
        """Clear published events (for testing)."""
        self.published_events.clear()


class EventBusFactory:
    """Factory for creating event bus instances."""
    
    _instances: Dict[str, AbstractEventBus] = {}
    
    @staticmethod
    async def create(
        broker_type: Optional[str] = None
    ) -> AbstractEventBus:
        """
        Create event bus instance.
        
        Args:
            broker_type: Type of broker (kafka, rabbitmq, mock)
                        If None, defaults from environment
        
        Returns:
            EventBus instance
        """
        if os.getenv("TESTING") == "1":
            broker_type = "mock"

        if broker_type is None:
            broker_type = os.getenv("EVENT_BUS", "mock").lower()
        
        # Return cached instance
        if broker_type in EventBusFactory._instances:
            return EventBusFactory._instances[broker_type]
        
        # Create new instance
        if broker_type == "kafka":
            from src.events.bus.kafka_bus import KafkaEventBus
            bus = KafkaEventBus()
        elif broker_type == "rabbitmq":
            from src.events.bus.rabbitmq_bus import RabbitMQEventBus
            bus = RabbitMQEventBus()
        else:
            bus = MockEventBus()
        
        EventBusFactory._instances[broker_type] = bus
        logger.info(f"Created event bus: {broker_type}")
        return bus
    
    @staticmethod
    def reset():
        """Reset factory (for testing)."""
        EventBusFactory._instances.clear()


# Global event bus instance
_event_bus: Optional[AbstractEventBus] = None


async def get_event_bus() -> AbstractEventBus:
    """Get or create global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = await EventBusFactory.create()
        await _event_bus.start()
    return _event_bus


async def shutdown_event_bus() -> None:
    """Shutdown global event bus."""
    global _event_bus
    if _event_bus:
        await _event_bus.stop()
        _event_bus = None
