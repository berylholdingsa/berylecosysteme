"""ESG domain event consumers."""

from src.events.base.event import DomainEvent, DomainEventType
from src.events.base.event_handler import EventHandler
from src.observability.logger import logger
from typing import Set


class EsgScoreComputedConsumer(EventHandler):
    """Consumes EsgScoreComputed events for analytics/reporting."""
    
    _processed: Set[str] = set()
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == DomainEventType.ESG_SCORE_COMPUTED
    
    async def handle(self, event: DomainEvent) -> None:
        if event.event_id in self._processed:
            return
        
        try:
            logger.info(f"EsgScoreComputedConsumer: Processing {event.event_id}")
            
            user_id = event.payload.get("user_id")
            score = event.payload.get("score")
            
            # TODO: Store in analytics database, trigger notifications
            
            self._processed.add(event.event_id)
        except Exception as e:
            logger.error(f"EsgScoreComputedConsumer error: {str(e)}")
