"""
Mapper for mobility AI engine API.

This module maps data between beryl-ai-engine responses and internal domain models.
Normalizes all external API responses to consistent internal format.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class DemandPrediction(BaseModel):
    """Normalized demand prediction model."""
    location: str
    predicted_demand: float
    confidence: float
    time_window: str
    forecast_horizon: int
    forecast_data: List[Dict[str, Any]]
    timestamp: datetime


class OptimizedRoute(BaseModel):
    """Normalized optimized route model."""
    route_id: str
    origin: str
    destination: str
    vehicle_type: str
    distance_km: float
    estimated_time_minutes: int
    energy_consumption_kwh: float
    waypoints: List[Dict[str, float]]
    efficiency_score: float
    timestamp: datetime


class FleetAnalysis(BaseModel):
    """Normalized fleet analysis model."""
    fleet_id: str
    total_vehicles: int
    active_vehicles: int
    utilization_rate: float
    avg_battery_health: float
    maintenance_alerts: List[Dict[str, Any]]
    key_insights: List[str]
    recommendations: List[str]
    timestamp: datetime


class VehicleStatus(BaseModel):
    """Normalized vehicle status model."""
    vehicle_id: str
    vehicle_type: str
    status: str
    battery_level: float
    location: Dict[str, float]
    available: bool
    last_updated: datetime


class MaintenancePrediction(BaseModel):
    """Normalized maintenance prediction model."""
    vehicle_id: str
    maintenance_needed: bool
    priority: str
    predicted_failure_component: Optional[str]
    recommended_action: str
    days_until_maintenance: Optional[int]
    timestamp: datetime


class MobilityMapper:
    """Maps beryl-ai-engine API responses to internal domain models."""

    @staticmethod
    def map_demand_response(external_response: Dict[str, Any]) -> DemandPrediction:
        """
        Map external demand prediction response to internal model.
        
        Args:
            external_response: Raw response from beryl-ai-engine
            
        Returns:
            Normalized DemandPrediction object
        """
        return DemandPrediction(
            location=external_response.get("location", ""),
            predicted_demand=float(external_response.get("predicted_demand", 0.0)),
            confidence=float(external_response.get("confidence", 0.0)),
            time_window=external_response.get("time_window", "hourly"),
            forecast_horizon=int(external_response.get("forecast_horizon", 24)),
            forecast_data=external_response.get("forecast_data", []),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_route_response(external_response: Dict[str, Any]) -> OptimizedRoute:
        """
        Map external route optimization response to internal model.
        
        Args:
            external_response: Raw response from beryl-ai-engine
            
        Returns:
            Normalized OptimizedRoute object
        """
        return OptimizedRoute(
            route_id=external_response.get("route_id", ""),
            origin=external_response.get("origin", ""),
            destination=external_response.get("destination", ""),
            vehicle_type=external_response.get("vehicle_type", ""),
            distance_km=float(external_response.get("distance_km", 0.0)),
            estimated_time_minutes=int(external_response.get("estimated_time_minutes", 0)),
            energy_consumption_kwh=float(external_response.get("energy_consumption_kwh", 0.0)),
            waypoints=external_response.get("waypoints", []),
            efficiency_score=float(external_response.get("efficiency_score", 0.0)),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_fleet_analysis_response(external_response: Dict[str, Any]) -> FleetAnalysis:
        """
        Map external fleet analysis response to internal model.
        
        Args:
            external_response: Raw response from beryl-ai-engine
            
        Returns:
            Normalized FleetAnalysis object
        """
        return FleetAnalysis(
            fleet_id=external_response.get("fleet_id", ""),
            total_vehicles=int(external_response.get("total_vehicles", 0)),
            active_vehicles=int(external_response.get("active_vehicles", 0)),
            utilization_rate=float(external_response.get("utilization_rate", 0.0)),
            avg_battery_health=float(external_response.get("avg_battery_health", 0.0)),
            maintenance_alerts=external_response.get("maintenance_alerts", []),
            key_insights=external_response.get("key_insights", []),
            recommendations=external_response.get("recommendations", []),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_vehicle_status_response(external_response: Dict[str, Any]) -> VehicleStatus:
        """
        Map external vehicle status response to internal model.
        
        Args:
            external_response: Raw response from beryl-ai-engine
            
        Returns:
            Normalized VehicleStatus object
        """
        return VehicleStatus(
            vehicle_id=external_response.get("vehicle_id", ""),
            vehicle_type=external_response.get("vehicle_type", ""),
            status=external_response.get("status", "unknown"),
            battery_level=float(external_response.get("battery_level", 0.0)),
            location=external_response.get("location", {"lat": 0.0, "lng": 0.0}),
            available=external_response.get("available", False),
            last_updated=datetime.fromisoformat(
                external_response.get("last_updated", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_maintenance_response(external_response: Dict[str, Any]) -> MaintenancePrediction:
        """
        Map external maintenance prediction response to internal model.
        
        Args:
            external_response: Raw response from beryl-ai-engine
            
        Returns:
            Normalized MaintenancePrediction object
        """
        return MaintenancePrediction(
            vehicle_id=external_response.get("vehicle_id", ""),
            maintenance_needed=external_response.get("maintenance_needed", False),
            priority=external_response.get("priority", "low"),
            predicted_failure_component=external_response.get("predicted_failure_component"),
            recommended_action=external_response.get("recommended_action", ""),
            days_until_maintenance=external_response.get("days_until_maintenance"),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )