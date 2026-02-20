"""Mobility domain event consumers."""

from src.events.base.event import DomainEvent, DomainEventType
from src.events.base.event_handler import EventHandler
from src.observability.logger import logger
from typing import Set


class RideCompletedConsumer(EventHandler):
    """Consumes RideCompleted events and updates user ESG metrics."""
    
    _processed: Set[str] = set()
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == DomainEventType.RIDE_COMPLETED
    
    async def handle(self, event: DomainEvent) -> None:
        if event.event_id in self._processed:
            return
        
        try:
            logger.info(f"RideCompletedConsumer: Processing {event.event_id}")
            
            user_id = event.payload.get("user_id")
            distance = event.payload.get("distance")
            
            # TODO: Update ESG scores, sustainability metrics
            
            self._processed.add(event.event_id)
        except Exception as e:
            logger.error(f"RideCompletedConsumer error: {str(e)}")
