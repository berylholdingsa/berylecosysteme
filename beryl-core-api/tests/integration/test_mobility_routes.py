"""
Integration tests for mobility routes.

Tests the complete flow from HTTP request to response normalization.
"""

import pytest
from datetime import datetime
from fastapi import HTTPException
from src.api.v1.routes.mobility_routes import router
from src.api.v1.routes import mobility_routes
from src.api.v1.schemas.mobility_schema import (
    DemandRequest, DemandResponse,
    RouteRequest, RouteResponse,
    FleetAnalysisRequest, FleetAnalysisResponse,
    IntelligentDestinationRequest,
)


@pytest.fixture
def demand_request():
    """Create a sample demand request."""
    return DemandRequest(
        location="Paris-Center",
        time_window="hourly",
        forecast_horizon=24
    )


@pytest.fixture
def demand_response():
    """Create a sample demand response."""
    return {
        "location": "Paris-Center",
        "predicted_demand": 150.5,
        "confidence": 0.92,
        "time_window": "hourly",
        "forecast_horizon": 24,
        "forecast_data": [
            {"hour": 0, "demand": 45.2},
            {"hour": 1, "demand": 42.1}
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def route_request():
    """Create a sample route optimization request."""
    return RouteRequest(
        origin="Paris-Gare-du-Nord",
        destination="Paris-LaDefense",
        vehicle_type="ebike",
        battery_level=85.0
    )


@pytest.fixture
def route_response():
    """Create a sample route response."""
    return {
        "route_id": "route_123",
        "origin": "Paris-Gare-du-Nord",
        "destination": "Paris-LaDefense",
        "vehicle_type": "ebike",
        "distance_km": 12.5,
        "estimated_time_minutes": 28,
        "energy_consumption_kwh": 0.45,
        "waypoints": [
            {"lat": 48.8806, "lng": 2.3553},
            {"lat": 48.8921, "lng": 2.3927}
        ],
        "efficiency_score": 0.87,
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def fleet_analysis_request():
    """Create a sample fleet analysis request."""
    return FleetAnalysisRequest(
        fleet_id="fleet_paris_001",
        metrics=["utilization", "battery_health"]
    )


@pytest.fixture
def fleet_analysis_response():
    """Create a sample fleet analysis response."""
    return {
        "fleet_id": "fleet_paris_001",
        "total_vehicles": 250,
        "active_vehicles": 198,
        "utilization_rate": 79.2,
        "avg_battery_health": 89.5,
        "maintenance_alerts": [
            {
                "vehicle_id": "vehicle_123",
                "component": "battery",
                "priority": "high"
            }
        ],
        "key_insights": [
            "Peak demand expected 16:00-19:00"
        ],
        "recommendations": [
            "Reposition 20 vehicles to downtown"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


class TestMobilityRoutes:
    """Test suite for mobility routes."""

    @pytest.mark.asyncio
    async def test_predict_demand_validation(self, demand_request):
        """Test demand prediction request validation."""
        assert demand_request.location == "Paris-Center"
        assert demand_request.time_window == "hourly"
        assert demand_request.forecast_horizon == 24

    @pytest.mark.asyncio
    async def test_optimize_route_validation(self, route_request):
        """Test route optimization request validation."""
        assert route_request.origin == "Paris-Gare-du-Nord"
        assert route_request.destination == "Paris-LaDefense"
        assert route_request.vehicle_type == "ebike"
        assert route_request.battery_level == 85.0

    @pytest.mark.asyncio
    async def test_fleet_analysis_validation(self, fleet_analysis_request):
        """Test fleet analysis request validation."""
        assert fleet_analysis_request.fleet_id == "fleet_paris_001"
        assert len(fleet_analysis_request.metrics) == 2

    def test_demand_response_normalization(self, demand_response):
        """Test demand response normalization."""
        response = DemandResponse(**demand_response)
        assert response.location == "Paris-Center"
        assert response.predicted_demand == 150.5
        assert response.confidence == 0.92
        assert len(response.forecast_data) == 2

    def test_route_response_normalization(self, route_response):
        """Test route response normalization."""
        response = RouteResponse(**route_response)
        assert response.route_id == "route_123"
        assert response.distance_km == 12.5
        assert response.energy_consumption_kwh == 0.45
        assert response.efficiency_score == 0.87
        assert len(response.waypoints) == 2

    def test_fleet_analysis_response_normalization(self, fleet_analysis_response):
        """Test fleet analysis response normalization."""
        response = FleetAnalysisResponse(**fleet_analysis_response)
        assert response.fleet_id == "fleet_paris_001"
        assert response.total_vehicles == 250
        assert response.active_vehicles == 198
        assert response.utilization_rate == 79.2
        assert len(response.maintenance_alerts) == 1
        assert len(response.key_insights) == 1

    def test_routes_are_registered(self):
        """Verify mobility routes are registered."""
        routes = router.routes
        route_paths = [r.path for r in routes if hasattr(r, 'path')]
        
        expected_paths = [
            "/demand/predict",
            "/routing/optimize",
            "/fleet/{fleet_id}/analyze",
            "/vehicle/{vehicle_id}/status",
            "/vehicle/{vehicle_id}/maintenance",
            "/fleet/{fleet_id}/optimize-distribution",
            "/destination/intelligent",
        ]
        
        for path in expected_paths:
            assert path in route_paths, f"Route {path} not found"

    def test_demand_request_with_defaults(self):
        """Test demand request with default values."""
        request = DemandRequest(location="Paris")
        assert request.location == "Paris"
        assert request.time_window == "hourly"
        assert request.forecast_horizon == 24

    def test_route_request_optional_constraints(self):
        """Test route request with optional constraints."""
        request = RouteRequest(
            origin="A",
            destination="B"
        )
        assert request.battery_level is None
        assert request.max_time_minutes is None

    def test_schema_field_validation(self):
        """Test schema field validation."""
        # Should work with valid data
        response = DemandResponse(
            location="Paris",
            predicted_demand=100.0,
            confidence=0.9,
            time_window="hourly",
            forecast_horizon=24,
            forecast_data=[],
            timestamp=datetime.utcnow()
        )
        assert response.confidence == 0.9

    def test_invalid_demand_request(self):
        """Test invalid demand request with missing required fields."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            # location is required
            DemandRequest()

    def test_workflow_integration_exists(self):
        """Verify workflow is properly integrated."""
        from src.orchestration.mobility.fleet_intelligence import FleetIntelligenceWorkflow
        
        workflow = FleetIntelligenceWorkflow()
        
        # Verify workflow methods exist
        assert hasattr(workflow, 'predict_demand')
        assert hasattr(workflow, 'optimize_route')
        assert hasattr(workflow, 'analyze_fleet')
        assert hasattr(workflow, 'get_vehicle_status')
        assert hasattr(workflow, 'predict_maintenance')
        assert hasattr(workflow, 'optimize_fleet_distribution')

    def test_mapper_integration_exists(self):
        """Verify mapper is properly integrated."""
        from src.adapters.mobility_ai_engine.mapper import MobilityMapper
        
        mapper = MobilityMapper()
        
        # Verify mapper methods exist
        assert hasattr(mapper, 'map_demand_response')
        assert hasattr(mapper, 'map_route_response')
        assert hasattr(mapper, 'map_fleet_analysis_response')
        assert hasattr(mapper, 'map_vehicle_status_response')
        assert hasattr(mapper, 'map_maintenance_response')

    def test_client_integration_exists(self):
        """Verify client is properly integrated."""
        from src.adapters.mobility_ai_engine.client import MobilityAIClient
        
        client = MobilityAIClient()
        
        # Verify client methods exist
        assert hasattr(client, 'predict_demand')
        assert hasattr(client, 'optimize_route')
        assert hasattr(client, 'analyze_fleet')
        assert hasattr(client, 'get_vehicle_status')
        assert hasattr(client, 'predict_maintenance')
        assert hasattr(client, 'close')


@pytest.mark.asyncio
async def test_intelligent_destination_requires_token(async_client):
    response = await async_client.post(
        "/api/v1/mobility/destination/intelligent",
        json={
            "user_id": "user-1",
            "origin": "Plateau",
            "query": "Marcory",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_intelligent_destination_rejects_wrong_scope(async_client, valid_tokens):
    response = await async_client.post(
        "/api/v1/mobility/destination/intelligent",
        headers={"Authorization": valid_tokens["social"]},
        json={
            "user_id": "user-1",
            "origin": "Plateau",
            "query": "Marcory",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


@pytest.mark.asyncio
async def test_intelligent_destination_success():
    request = IntelligentDestinationRequest(
        user_id="user-1",
        origin="Plateau",
        query="Marcory Zone 4",
        candidate_destinations=[
            "Marcory Zone 4",
            "Cocody Riviera",
            "Aeroport Felix Houphouet-Boigny",
        ],
        trip_history=[],
        travel_mode="eco",
        traffic_level="moderate",
        weather_risk="low",
        battery_level=62,
        is_recurring=True,
        hour_of_day=18,
    )

    response = await mobility_routes.intelligent_destination(request)

    assert response.selected_destination
    assert 0 <= response.confidence <= 1
    assert len(response.alternatives) >= 1
    assert response.aoq.dispatch_recommendation
    assert response.aoq.decision in {"APPROVE", "REVIEW", "DEFER"}
    assert response.simulation.route_id
    assert response.simulation.estimated_time_minutes >= 0
    assert response.simulation.estimated_price_xof >= 0


@pytest.mark.asyncio
async def test_intelligent_destination_validation_error():
    request = IntelligentDestinationRequest(
        user_id="user-1",
        origin="Plateau",
        query="   ",
        candidate_destinations=[],
        trip_history=[],
    )

    with pytest.raises(HTTPException) as exc:
        await mobility_routes.intelligent_destination(request)

    assert exc.value.status_code == 400
    assert "at least one destination candidate" in str(exc.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
