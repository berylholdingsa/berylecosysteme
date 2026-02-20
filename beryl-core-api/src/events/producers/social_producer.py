"""Social domain event producers."""

from src.events.base.event import PostCreatedEvent, FeedGeneratedEvent, ContentFlaggedEvent
from src.events.bus.event_bus import get_event_bus
from src.observability.logger import logger
from typing import Any


class SocialEventProducer:
    """Produces events from Social domain."""
    
    @staticmethod
    async def post_created(post_id: str, user_id: str, **extra: Any):
        event = PostCreatedEvent(
            payload={"post_id": post_id, "user_id": user_id, **extra},
            metadata={"user_id": user_id}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"Social: Post created - {post_id}")
    
    @staticmethod
    async def feed_generated(user_id: str, item_count: int, **extra: Any):
        event = FeedGeneratedEvent(
            payload={"user_id": user_id, "item_count": item_count, **extra},
            metadata={"user_id": user_id}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"Social: Feed generated - {user_id}")
    
    @staticmethod
    async def content_flagged(content_id: str, reason: str, **extra: Any):
        event = ContentFlaggedEvent(
            payload={"content_id": content_id, "reason": reason, **extra},
            metadata={}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.warning(f"Social: Content flagged - {content_id}")
