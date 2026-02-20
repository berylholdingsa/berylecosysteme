"""
Fleet Intelligence Workflow for Mobility Operations.

Orchestrates demand prediction, route optimization, and fleet analysis.
Coordinates between beryl-core-api and beryl-ai-engine.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from src.adapters.mobility_ai_engine.client import MobilityAIClient
from src.adapters.mobility_ai_engine.mapper import (
    MobilityMapper,
    DemandPrediction,
    OptimizedRoute,
    FleetAnalysis,
    VehicleStatus,
    MaintenancePrediction
)
from src.observability.logger import logger


class FleetIntelligenceWorkflow:
    """Orchestrates mobility intelligence operations."""

    def __init__(self):
        self.client = MobilityAIClient()
        self.mapper = MobilityMapper()

    async def predict_demand(
        self,
        location: str,
        time_window: str = "hourly",
        forecast_horizon: int = 24
    ) -> DemandPrediction:
        """
        Predict demand for electric mobility at a location.
        
        Workflow:
        1. Call beryl-ai-engine demand prediction API
        2. Map response to internal DemandPrediction model
        3. Validate and log prediction
        
        Args:
            location: Geographic location
            time_window: Granularity of prediction
            forecast_horizon: Hours to forecast
            
        Returns:
            Normalized DemandPrediction
        """
        logger.info(f"Predicting demand for location: {location}")
        
        raw_response = await self.client.predict_demand(
            location=location,
            time_window=time_window,
            forecast_horizon=forecast_horizon
        )
        
        prediction = self.mapper.map_demand_response(raw_response)
        logger.info(f"Demand prediction completed: {prediction.predicted_demand} units")
        
        return prediction

    async def optimize_route(
        self,
        origin: str,
        destination: str,
        vehicle_type: str = "ebike",
        battery_level: Optional[float] = None,
        max_time_minutes: Optional[int] = None
    ) -> OptimizedRoute:
        """
        Optimize route for energy efficiency.
        
        Workflow:
        1. Build constraints from optional parameters
        2. Call beryl-ai-engine route optimization API
        3. Map response to internal OptimizedRoute model
        4. Validate efficiency score
        
        Args:
            origin: Starting point
            destination: Ending point
            vehicle_type: Type of vehicle (ebike, escooter, ecar)
            battery_level: Current battery percentage (0-100)
            max_time_minutes: Maximum allowed travel time
            
        Returns:
            Normalized OptimizedRoute with efficiency metrics
        """
        logger.info(f"Optimizing route from {origin} to {destination}")
        
        constraints = {}
        if battery_level is not None:
            constraints["battery_level"] = battery_level
        if max_time_minutes is not None:
            constraints["max_time_minutes"] = max_time_minutes
        
        raw_response = await self.client.optimize_route(
            origin=origin,
            destination=destination,
            vehicle_type=vehicle_type,
            constraints=constraints
        )
        
        route = self.mapper.map_route_response(raw_response)
        logger.info(
            f"Route optimized: {route.distance_km}km, "
            f"energy: {route.energy_consumption_kwh}kWh, "
            f"efficiency: {route.efficiency_score}"
        )
        
        return route

    async def analyze_fleet(
        self,
        fleet_id: str,
        metrics: Optional[List[str]] = None
    ) -> FleetAnalysis:
        """
        Analyze fleet intelligence metrics.
        
        Workflow:
        1. Call beryl-ai-engine fleet analysis API
        2. Map response to internal FleetAnalysis model
        3. Extract key insights and recommendations
        4. Log critical maintenance alerts
        
        Args:
            fleet_id: Fleet identifier
            metrics: Specific metrics to analyze
            
        Returns:
            Comprehensive FleetAnalysis with insights
        """
        logger.info(f"Analyzing fleet: {fleet_id}")
        
        raw_response = await self.client.analyze_fleet(
            fleet_id=fleet_id,
            metrics=metrics
        )
        
        analysis = self.mapper.map_fleet_analysis_response(raw_response)
        
        if analysis.maintenance_alerts:
            logger.warning(
                f"Fleet {fleet_id} has {len(analysis.maintenance_alerts)} maintenance alerts"
            )
        
        logger.info(
            f"Fleet analysis complete: {analysis.utilization_rate}% utilization, "
            f"{analysis.avg_battery_health}% avg battery health"
        )
        
        return analysis

    async def get_vehicle_status(
        self,
        vehicle_id: str
    ) -> VehicleStatus:
        """
        Get real-time vehicle status.
        
        Workflow:
        1. Call beryl-ai-engine vehicle status API
        2. Map response to internal VehicleStatus model
        3. Log availability status
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            Normalized VehicleStatus
        """
        logger.info(f"Fetching status for vehicle: {vehicle_id}")
        
        raw_response = await self.client.get_vehicle_status(vehicle_id)
        status = self.mapper.map_vehicle_status_response(raw_response)
        
        logger.info(
            f"Vehicle {vehicle_id} status: {status.status}, "
            f"battery: {status.battery_level}%"
        )
        
        return status

    async def predict_maintenance(
        self,
        vehicle_id: str
    ) -> MaintenancePrediction:
        """
        Predict maintenance needs for a vehicle.
        
        Workflow:
        1. Call beryl-ai-engine maintenance prediction API
        2. Map response to internal MaintenancePrediction model
        3. Alert if high priority maintenance detected
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            Normalized MaintenancePrediction
        """
        logger.info(f"Predicting maintenance for vehicle: {vehicle_id}")
        
        raw_response = await self.client.predict_maintenance(vehicle_id)
        prediction = self.mapper.map_maintenance_response(raw_response)
        
        if prediction.maintenance_needed and prediction.priority in ["high", "critical"]:
            logger.warning(
                f"High priority maintenance needed for {vehicle_id}: "
                f"{prediction.predicted_failure_component}"
            )
        
        return prediction

    async def optimize_fleet_distribution(
        self,
        fleet_id: str,
        target_locations: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize vehicle distribution across target locations.
        
        Workflow:
        1. Analyze current fleet state
        2. Predict demand at target locations
        3. Calculate optimal vehicle movements
        4. Return distribution plan
        
        Args:
            fleet_id: Fleet identifier
            target_locations: Locations needing vehicles
            
        Returns:
            Distribution plan with vehicle reassignments
        """
        logger.info(f"Optimizing distribution for fleet {fleet_id}")
        
        fleet_analysis = await self.analyze_fleet(fleet_id)
        demand_predictions = []
        
        for location in target_locations:
            demand = await self.predict_demand(location)
            demand_predictions.append({
                "location": location,
                "predicted_demand": demand.predicted_demand
            })
        
        distribution_plan = {
            "fleet_id": fleet_id,
            "timestamp": datetime.utcnow().isoformat(),
            "current_state": {
                "total_vehicles": fleet_analysis.total_vehicles,
                "active_vehicles": fleet_analysis.active_vehicles,
                "utilization_rate": fleet_analysis.utilization_rate
            },
            "demand_forecast": demand_predictions,
            "recommendations": fleet_analysis.recommendations
        }
        
        logger.info(f"Distribution plan generated for {fleet_id}")
        return distribution_plan

    async def close(self):
        """Close client connections."""
        await self.client.close()
