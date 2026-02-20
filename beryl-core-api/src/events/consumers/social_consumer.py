"""Social domain event consumers."""

from src.events.base.event import DomainEvent, DomainEventType
from src.events.base.event_handler import EventHandler
from src.observability.logger import logger
from typing import Set


class ContentFlaggedConsumer(EventHandler):
    """Consumes ContentFlagged events for moderation."""
    
    _processed: Set[str] = set()
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == DomainEventType.CONTENT_FLAGGED
    
    async def handle(self, event: DomainEvent) -> None:
        if event.event_id in self._processed:
            return
        
        try:
            logger.warning(f"ContentFlaggedConsumer: Processing {event.event_id}")
            
            content_id = event.payload.get("content_id")
            reason = event.payload.get("reason")
            
            # TODO: Route to moderation queue, log violation
            
            self._processed.add(event.event_id)
        except Exception as e:
            logger.error(f"ContentFlaggedConsumer error: {str(e)}")
