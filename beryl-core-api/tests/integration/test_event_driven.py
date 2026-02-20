"""
Integration tests for event-driven architecture.

Tests publisher/subscriber pattern with mock event bus.
"""

import pytest
import asyncio
from src.events.base.event import (
    DomainEvent,
    DomainEventType,
    TransactionCompletedEvent,
    RideCompletedEvent,
)
from src.events.bus.event_bus import MockEventBus, EventBusFactory
from src.events.consumers.fintech_consumer import TransactionCompletedConsumer
from src.events.consumers.mobility_consumer import RideCompletedConsumer


class TestEventPublishing:
    """Test event publishing."""
    
    @pytest.mark.asyncio
    async def test_publish_transaction_completed(self):
        """Test publishing TransactionCompleted event."""
        bus = MockEventBus()
        await bus.start()
        
        event = TransactionCompletedEvent(
            payload={
                "transaction_id": "tx_123",
                "user_id": "user_456",
                "amount": 100.0
            },
            metadata={"user_id": "user_456"}
        )
        
        await bus.publish(event)
        
        published = bus.get_published_events()
        assert len(published) == 1
        assert published[0].event_type == DomainEventType.TRANSACTION_COMPLETED
        assert published[0].payload["transaction_id"] == "tx_123"
        
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_event_immutability(self):
        """Test that events are immutable."""
        event = TransactionCompletedEvent(
            payload={"transaction_id": "tx_123"},
            metadata={"user_id": "user_456"}
        )
        
        # Attempt to modify should fail
        with pytest.raises(Exception):  # Pydantic frozen model
            event.payload["transaction_id"] = "different"


class TestEventSubscription:
    """Test event subscription and handling."""
    
    @pytest.mark.asyncio
    async def test_handler_receives_event(self):
        """Test that handlers receive published events."""
        bus = MockEventBus()
        consumer = TransactionCompletedConsumer()
        
        await bus.subscribe(DomainEventType.TRANSACTION_COMPLETED, consumer)
        await bus.start()
        
        event = TransactionCompletedEvent(
            payload={"transaction_id": "tx_123"},
            metadata={"user_id": "user_456"}
        )
        
        await bus.publish(event)
        
        # Check that handler processed it
        assert event.event_id in consumer._processed
        
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_consumers(self):
        """Test multiple consumers processing same event."""
        bus = MockEventBus()
        consumer1 = TransactionCompletedConsumer()
        consumer2 = TransactionCompletedConsumer()
        
        await bus.subscribe(DomainEventType.TRANSACTION_COMPLETED, consumer1)
        await bus.subscribe(DomainEventType.TRANSACTION_COMPLETED, consumer2)
        await bus.start()
        
        event = TransactionCompletedEvent(
            payload={"transaction_id": "tx_123"},
            metadata={"user_id": "user_456"}
        )
        
        await bus.publish(event)
        
        # Both consumers should process
        assert event.event_id in consumer1._processed
        assert event.event_id in consumer2._processed
        
        await bus.stop()


class TestEventIdempotency:
    """Test idempotent event handling."""
    
    @pytest.mark.asyncio
    async def test_consumer_idempotency(self):
        """Test that consuming same event twice doesn't cause issues."""
        consumer = TransactionCompletedConsumer()
        
        event = TransactionCompletedEvent(
            payload={"transaction_id": "tx_123"},
            metadata={"user_id": "user_456"}
        )
        
        # Handle same event twice
        await consumer.handle(event)
        await consumer.handle(event)
        
        # Should only be in processed set once
        assert event.event_id in consumer._processed
        assert len(consumer.handled_events) == 1


class TestCrossDomainEvents:
    """Test cross-domain event communication."""
    
    @pytest.mark.asyncio
    async def test_mobility_event_consumed_in_esg(self):
        """Test that Mobility events can be consumed by ESG domain."""
        bus = MockEventBus()
        mobility_consumer = RideCompletedConsumer()
        
        await bus.subscribe(DomainEventType.RIDE_COMPLETED, mobility_consumer)
        await bus.start()
        
        event = RideCompletedEvent(
            payload={"ride_id": "ride_789", "user_id": "user_456", "distance": 5.5},
            metadata={"user_id": "user_456"}
        )
        
        await bus.publish(event)
        
        assert event.event_id in mobility_consumer._processed
        
        await bus.stop()


class TestEventSerialization:
    """Test event serialization."""
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = TransactionCompletedEvent(
            payload={"transaction_id": "tx_123", "amount": 100.0},
            metadata={"user_id": "user_456"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "fintech.transaction.completed"
        assert event_dict["domain"] == "fintech"
        assert event_dict["payload"]["transaction_id"] == "tx_123"
        assert isinstance(event_dict["timestamp"], str)


class TestEventBusFactory:
    """Test event bus factory."""
    
    @pytest.mark.asyncio
    async def test_factory_creates_mock_bus(self):
        """Test factory creates mock bus by default."""
        EventBusFactory.reset()
        bus = await EventBusFactory.create(broker_type="mock")
        
        assert bus is not None
        assert bus.broker_type == "mock"
        
        await bus.start()
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_factory_caches_instances(self):
        """Test factory caches bus instances."""
        EventBusFactory.reset()
        
        bus1 = await EventBusFactory.create(broker_type="mock")
        bus2 = await EventBusFactory.create(broker_type="mock")
        
        assert bus1 is bus2


class TestEventBusStats:
    """Test event bus statistics."""
    
    @pytest.mark.asyncio
    async def test_bus_statistics(self):
        """Test bus collects statistics."""
        bus = MockEventBus()
        consumer = TransactionCompletedConsumer()
        
        await bus.subscribe(DomainEventType.TRANSACTION_COMPLETED, consumer)
        await bus.start()
        
        event = TransactionCompletedEvent(
            payload={"transaction_id": "tx_123"},
            metadata={}
        )
        
        await bus.publish(event)
        
        stats = bus.get_stats()
        
        assert stats["broker_type"] == "mock"
        assert stats["is_running"] is True
        assert stats["events_published"] == 1
        assert stats["errors"] == 0
        
        await bus.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
