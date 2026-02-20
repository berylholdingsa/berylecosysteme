"""Mobility domain event producers."""

from src.events.base.event import RideCompletedEvent, FleetOptimizedEvent, DemandPredictedEvent
from src.events.bus.event_bus import get_event_bus
from src.observability.logger import logger
from typing import Any, Optional


class MobilityEventProducer:
    """Produces events from Mobility domain."""
    
    @staticmethod
    async def ride_completed(ride_id: str, user_id: str, distance: float, **extra: Any):
        event = RideCompletedEvent(
            payload={"ride_id": ride_id, "user_id": user_id, "distance": distance, **extra},
            metadata={"user_id": user_id}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"Mobility: Ride completed - {ride_id}")
    
    @staticmethod
    async def fleet_optimized(fleet_id: str, optimization_score: float, **extra: Any):
        event = FleetOptimizedEvent(
            payload={"fleet_id": fleet_id, "optimization_score": optimization_score, **extra},
            metadata={}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"Mobility: Fleet optimized - {fleet_id}")
    
    @staticmethod
    async def demand_predicted(location: str, demand: float, **extra: Any):
        event = DemandPredictedEvent(
            payload={"location": location, "demand": demand, **extra},
            metadata={}
        )
        bus = await get_event_bus()
        await bus.publish(event)
        logger.info(f"Mobility: Demand predicted - {location}")
