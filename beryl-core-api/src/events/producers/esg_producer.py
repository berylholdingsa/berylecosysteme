"""ESG domain event producers."""

from src.events.base.event import EsgScoreComputedEvent, PedometerUpdatedEvent
from src.events.bus.event_bus import get_event_bus
from src.observability.logger import logger
from typing import Any


class EsgEventProducer:
    """Produces events from ESG domain."""
    
    @staticmethod
    async def esg_score_computed(user_id: str, score: float, **extra: Any):
        event = EsgScoreComputedEvent(
            payload={"user_id": user_id, "score": score, **extra},
            metadata={"user_id": user_id}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"ESG: Score computed - {user_id}")
    
    @staticmethod
    async def pedometer_updated(user_id: str, steps: int, **extra: Any):
        event = PedometerUpdatedEvent(
            payload={"user_id": user_id, "steps": steps, **extra},
            metadata={"user_id": user_id}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"ESG: Pedometer updated - {user_id}")
