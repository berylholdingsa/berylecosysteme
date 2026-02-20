"""
Central event registry for domain event handlers.

Registers all consumers with the event bus.
Called during application startup.
"""

from src.events.bus.event_bus import get_event_bus, AbstractEventBus
from src.events.base.event import DomainEventType
from src.events.consumers.fintech_consumer import TransactionCompletedConsumer, PaymentFailedConsumer
from src.events.consumers.mobility_consumer import RideCompletedConsumer
from src.events.consumers.esg_consumer import EsgScoreComputedConsumer
from src.events.consumers.social_consumer import ContentFlaggedConsumer
from src.observability.logger import logger


async def register_all_handlers(bus: AbstractEventBus) -> None:
    """Register all domain event handlers with the event bus."""
    
    logger.info("Registering all event handlers...")
    
    # Fintech consumers
    await bus.subscribe(DomainEventType.TRANSACTION_COMPLETED, TransactionCompletedConsumer())
    await bus.subscribe(DomainEventType.PAYMENT_FAILED, PaymentFailedConsumer())
    
    # Mobility consumers
    await bus.subscribe(DomainEventType.RIDE_COMPLETED, RideCompletedConsumer())
    
    # ESG consumers
    await bus.subscribe(DomainEventType.ESG_SCORE_COMPUTED, EsgScoreComputedConsumer())
    
    # Social consumers
    await bus.subscribe(DomainEventType.CONTENT_FLAGGED, ContentFlaggedConsumer())
    
    # TODO: Add more consumers for other event types
    #       - Analytics consumers
    #       - Audit consumers
    #       - Compliance consumers
    
    logger.info("All event handlers registered")


async def initialize_event_system() -> None:
    """Initialize the entire event-driven system."""
    logger.info("Initializing event-driven architecture...")
    
    bus = await get_event_bus()
    await register_all_handlers(bus)
    
    stats = bus.get_stats()
    logger.info(f"Event system initialized: {stats}")


async def shutdown_event_system() -> None:
    """Shutdown the event system."""
    from src.events.bus.event_bus import shutdown_event_bus
    await shutdown_event_bus()
    logger.info("Event system shutdown complete")
