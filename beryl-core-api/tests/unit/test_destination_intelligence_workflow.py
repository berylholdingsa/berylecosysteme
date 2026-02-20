"""Unit tests for mobility destination intelligence workflow."""

from src.api.v1.schemas.mobility_schema import DestinationHistoryItem
from src.orchestration.mobility.destination_intelligence import (
    DestinationIntelligenceWorkflow,
    MobilityDestinationValidationError,
)


def test_destination_workflow_returns_ranked_recommendation():
    workflow = DestinationIntelligenceWorkflow()

    result = workflow.evaluate(
        user_id="user-1",
        origin="Plateau",
        query="Cocody Riviera",
        candidate_destinations=["Cocody Riviera", "Marcory Zone 4", "Aeroport"],
        trip_history=[
            DestinationHistoryItem(destination="Cocody Riviera", count=5, last_used_hours=12),
            DestinationHistoryItem(destination="Marcory Zone 4", count=2, last_used_hours=48),
        ],
        travel_mode="eco",
        traffic_level="moderate",
        weather_risk="low",
        battery_level=72,
        is_recurring=True,
        hour_of_day=8,
    )

    assert result.selected_destination
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.alternatives) >= 1
    assert result.alternatives[0].destination == result.selected_destination
    assert 0.0 <= result.aoq.mobility_score <= 100.0
    assert 0.0 <= result.aoq.esg_score <= 100.0
    assert result.aoq.decision in {"APPROVE", "REVIEW", "DEFER"}
    assert result.simulation.route_id
    assert result.simulation.estimated_price_xof >= 0


def test_destination_workflow_uses_safety_dispatch_on_high_weather_risk():
    workflow = DestinationIntelligenceWorkflow()

    result = workflow.evaluate(
        user_id="user-2",
        origin="Plateau",
        query="Marcory",
        candidate_destinations=["Marcory"],
        trip_history=[],
        travel_mode="solo",
        traffic_level="low",
        weather_risk="high",
        battery_level=90,
        is_recurring=False,
        hour_of_day=15,
    )

    assert result.aoq.dispatch_recommendation == "safety_mode"


def test_destination_workflow_raises_for_empty_candidate_pool():
    workflow = DestinationIntelligenceWorkflow()

    try:
        workflow.evaluate(
            user_id="user-3",
            origin="Plateau",
            query="   ",
            candidate_destinations=["", "   "],
            trip_history=[],
            travel_mode="solo",
            traffic_level="low",
            weather_risk="low",
            battery_level=50,
            is_recurring=False,
            hour_of_day=10,
        )
    except MobilityDestinationValidationError as exc:
        assert "at least one destination candidate" in str(exc)
    else:
        raise AssertionError("Expected MobilityDestinationValidationError")
