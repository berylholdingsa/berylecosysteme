"""
Schemas for mobility operations.

This module defines Pydantic models for mobility-related API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime


class DemandRequest(BaseModel):
    """Request model for demand prediction."""
    location: str = Field(..., description="Geographic location identifier")
    time_window: str = Field(default="hourly", description="Granularity: hourly, daily, weekly")
    forecast_horizon: int = Field(default=24, description="Hours ahead to forecast")


class DemandResponse(BaseModel):
    """Response model for demand prediction."""
    location: str
    predicted_demand: float = Field(..., description="Predicted demand units")
    confidence: float = Field(..., description="Confidence score 0-1")
    time_window: str
    forecast_horizon: int
    forecast_data: List[Dict[str, Any]]
    timestamp: datetime


class RouteRequest(BaseModel):
    """Request model for route optimization."""
    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Ending location")
    vehicle_type: str = Field(default="ebike", description="Type of vehicle")
    battery_level: Optional[float] = Field(None, description="Current battery percentage 0-100")
    max_time_minutes: Optional[int] = Field(None, description="Maximum travel time")


class RouteResponse(BaseModel):
    """Response model for optimized route."""
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


class FleetAnalysisRequest(BaseModel):
    """Request model for fleet analysis."""
    fleet_id: str = Field(..., description="Fleet identifier")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to analyze")


class FleetAnalysisResponse(BaseModel):
    """Response model for fleet analysis."""
    fleet_id: str
    total_vehicles: int
    active_vehicles: int
    utilization_rate: float = Field(..., description="Percentage 0-100")
    avg_battery_health: float = Field(..., description="Average battery health percentage")
    maintenance_alerts: List[Dict[str, Any]]
    key_insights: List[str]
    recommendations: List[str]
    timestamp: datetime


class VehicleStatusRequest(BaseModel):
    """Request model for vehicle status."""
    vehicle_id: str = Field(..., description="Vehicle identifier")


class VehicleStatusResponse(BaseModel):
    """Response model for vehicle status."""
    vehicle_id: str
    vehicle_type: str
    status: str = Field(..., description="available, in_use, maintenance, offline")
    battery_level: float = Field(..., description="Battery percentage 0-100")
    location: Dict[str, float] = Field(..., description="GPS coordinates {lat, lng}")
    available: bool
    last_updated: datetime


class MaintenancePredictionRequest(BaseModel):
    """Request model for maintenance prediction."""
    vehicle_id: str = Field(..., description="Vehicle identifier")


class MaintenancePredictionResponse(BaseModel):
    """Response model for maintenance prediction."""
    vehicle_id: str
    maintenance_needed: bool
    priority: str = Field(..., description="low, medium, high, critical")
    predicted_failure_component: Optional[str]
    recommended_action: str
    days_until_maintenance: Optional[int]
    timestamp: datetime


class FleetDistributionRequest(BaseModel):
    """Request model for fleet distribution optimization."""
    fleet_id: str = Field(..., description="Fleet identifier")
    target_locations: List[str] = Field(..., description="Locations needing vehicles")


class FleetDistributionResponse(BaseModel):
    """Response model for fleet distribution plan."""
    fleet_id: str
    timestamp: datetime
    current_state: Dict[str, Any]
    demand_forecast: List[Dict[str, Any]]
    recommendations: List[str]


class DestinationHistoryItem(BaseModel):
    """Historical destination usage signal used by AOQ mobility scoring."""

    destination: str = Field(..., min_length=1, max_length=128)
    count: int = Field(default=1, ge=1, le=1000)
    last_used_hours: Optional[int] = Field(
        default=None,
        ge=0,
        le=24 * 365,
        description="Hours since last usage of this destination",
    )


class IntelligentDestinationRequest(BaseModel):
    """Request payload for smart destination recommendation."""

    user_id: str = Field(..., min_length=1, max_length=128)
    origin: str = Field(..., min_length=1, max_length=128)
    query: str = Field(..., min_length=1, max_length=128)
    candidate_destinations: List[str] = Field(default_factory=list, max_length=20)
    trip_history: List[DestinationHistoryItem] = Field(default_factory=list, max_length=50)
    travel_mode: Literal["solo", "family", "eco"] = "solo"
    traffic_level: Literal["low", "moderate", "high"] = "moderate"
    weather_risk: Literal["low", "medium", "high"] = "low"
    battery_level: Optional[float] = Field(default=None, ge=0, le=100)
    is_recurring: bool = False
    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23)


class IntelligentDestinationAlternative(BaseModel):
    """Alternative destination ranked by backend AOQ mobility logic."""

    destination: str
    confidence: float = Field(..., ge=0, le=1)
    score: float = Field(..., ge=0, le=1)


class IntelligentDestinationAoq(BaseModel):
    """AOQ decision details for mobility routing and dispatch optimization."""

    mobility_score: float = Field(..., ge=0, le=100)
    esg_score: float = Field(..., ge=0, le=100)
    dispatch_recommendation: str
    decision: str
    rationale: str


class IntelligentDestinationSimulation(BaseModel):
    """Simulation preview returned for selected destination."""

    route_id: str
    distance_km: float = Field(..., ge=0)
    estimated_time_minutes: int = Field(..., ge=0)
    estimated_price_xof: int = Field(..., ge=0)
    energy_kwh: float = Field(..., ge=0)
    co2_saved_kg: float = Field(..., ge=0)


class IntelligentDestinationResponse(BaseModel):
    """Response payload for smart destination recommendation."""

    selected_destination: str
    confidence: float = Field(..., ge=0, le=1)
    alternatives: List[IntelligentDestinationAlternative]
    aoq: IntelligentDestinationAoq
    simulation: IntelligentDestinationSimulation
    timestamp: datetime


class RideQuoteRequest(BaseModel):
    """Request payload for backend-only ride quoting."""

    rider_id: str = Field(..., min_length=1, max_length=128)
    pickup_label: str = Field(..., min_length=1, max_length=128)
    dropoff_label: str = Field(..., min_length=1, max_length=128)
    service_tier: Literal["standard", "comfort", "premium"] = "standard"


class RideConfidenceInterval(BaseModel):
    lower: int = Field(..., ge=0)
    upper: int = Field(..., ge=0)


class RideExplainabilityFactor(BaseModel):
    name: str
    weight: float = Field(..., ge=0, le=1)
    value: Any


class RideExplainability(BaseModel):
    summary: str
    factors: List[RideExplainabilityFactor]


class RideQuoteResponse(BaseModel):
    quote_id: str
    rider_id: str
    pickup_label: str
    dropoff_label: str
    service_tier: str
    distance_km: float = Field(..., ge=0)
    estimated_eta_minutes: int = Field(..., ge=0)
    estimated_price_xof: int = Field(..., ge=0)
    pricing_model_version: str
    confidence_interval: RideConfidenceInterval
    explainability: RideExplainability
    co2_saved_kg: float = Field(..., ge=0)
    expires_at: datetime


class RideBookRequest(BaseModel):
    quote_id: str = Field(..., min_length=8, max_length=64)
    rider_id: str = Field(..., min_length=1, max_length=128)


class RideAssignRequest(BaseModel):
    ride_id: str = Field(..., min_length=8, max_length=64)
    driver_id: Optional[str] = Field(default=None, min_length=3, max_length=128)


class RideCancelRequest(BaseModel):
    ride_id: str = Field(..., min_length=8, max_length=64)
    reason: str = Field(default="user_cancelled", min_length=3, max_length=256)


class RideCompleteRequest(BaseModel):
    ride_id: str = Field(..., min_length=8, max_length=64)
    distance_km: Optional[float] = Field(default=None, ge=0)
    duration_minutes: Optional[int] = Field(default=None, ge=0)


class RideStateResponse(BaseModel):
    ride_id: str
    quote_id: str
    rider_id: str
    driver_id: Optional[str]
    status: Literal["BOOKED", "ASSIGNED", "CANCELLED", "COMPLETED"]
    pickup_label: str
    dropoff_label: str
    service_tier: str
    distance_km: float = Field(..., ge=0)
    estimated_eta_minutes: int = Field(..., ge=0)
    estimated_price_xof: int = Field(..., ge=0)
    final_price_xof: Optional[int] = Field(default=None, ge=0)
    pricing_model_version: str
    confidence_interval: RideConfidenceInterval
    explainability: RideExplainability
    co2_saved_kg: float = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
