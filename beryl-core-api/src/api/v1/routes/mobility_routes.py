"""
Mobility routes for the Beryl Core API.

Exposes REST endpoints for electric mobility operations.
Routes orchestrate requests through the mobility workflow.
"""

from fastapi import APIRouter, HTTPException, Header, Request, Security, status
from fastapi.security import HTTPBearer
from src.orchestration.mobility.fleet_intelligence import FleetIntelligenceWorkflow
from src.orchestration.mobility.destination_intelligence import (
    DestinationIntelligenceWorkflow,
    MobilityDestinationValidationError,
)
from src.orchestration.mobility.ride_lifecycle import (
    RideLifecycleError,
    RideLifecycleService,
)
from src.api.v1.schemas.mobility_schema import (
    DemandRequest, DemandResponse,
    RouteRequest, RouteResponse,
    FleetAnalysisRequest, FleetAnalysisResponse,
    VehicleStatusRequest, VehicleStatusResponse,
    MaintenancePredictionRequest, MaintenancePredictionResponse,
    FleetDistributionRequest, FleetDistributionResponse,
    IntelligentDestinationRequest, IntelligentDestinationResponse,
    IntelligentDestinationAlternative, IntelligentDestinationAoq,
    IntelligentDestinationSimulation,
    RideQuoteRequest, RideQuoteResponse,
    RideBookRequest, RideAssignRequest, RideCancelRequest, RideCompleteRequest,
    RideStateResponse,
)
from src.events.bus.event_bus import get_event_bus
from src.observability.logger import logger

router = APIRouter()
workflow = FleetIntelligenceWorkflow()
destination_workflow = DestinationIntelligenceWorkflow()
ride_lifecycle_service = RideLifecycleService()
security = HTTPBearer()


@router.post("/demand/predict", response_model=DemandResponse, dependencies=[Security(security)])
async def predict_demand(request: DemandRequest):
    """
    Predict demand for electric mobility at a location.
    
    - **location**: Geographic location identifier
    - **time_window**: hourly, daily, or weekly granularity
    - **forecast_horizon**: Number of hours to forecast ahead
    """
    try:
        logger.info(f"Demand prediction request: {request.location}")
        prediction = await workflow.predict_demand(
            location=request.location,
            time_window=request.time_window,
            forecast_horizon=request.forecast_horizon
        )
        return DemandResponse(
            location=prediction.location,
            predicted_demand=prediction.predicted_demand,
            confidence=prediction.confidence,
            time_window=prediction.time_window,
            forecast_horizon=prediction.forecast_horizon,
            forecast_data=prediction.forecast_data,
            timestamp=prediction.timestamp
        )
    except Exception as e:
        logger.error(f"Demand prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict demand"
        )


@router.post("/routing/optimize", response_model=RouteResponse)
async def optimize_route(request: RouteRequest):
    """
    Optimize route for energy efficiency.
    
    - **origin**: Starting location
    - **destination**: Ending location
    - **vehicle_type**: ebike, escooter, or ecar
    - **battery_level**: Current battery percentage (optional)
    - **max_time_minutes**: Maximum allowed travel time (optional)
    """
    try:
        logger.info(f"Route optimization request: {request.origin} -> {request.destination}")
        route = await workflow.optimize_route(
            origin=request.origin,
            destination=request.destination,
            vehicle_type=request.vehicle_type,
            battery_level=request.battery_level,
            max_time_minutes=request.max_time_minutes
        )
        return RouteResponse(
            route_id=route.route_id,
            origin=route.origin,
            destination=route.destination,
            vehicle_type=route.vehicle_type,
            distance_km=route.distance_km,
            estimated_time_minutes=route.estimated_time_minutes,
            energy_consumption_kwh=route.energy_consumption_kwh,
            waypoints=route.waypoints,
            efficiency_score=route.efficiency_score,
            timestamp=route.timestamp
        )
    except Exception as e:
        logger.error(f"Route optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize route"
        )


@router.post("/fleet/{fleet_id}/analyze", response_model=FleetAnalysisResponse)
async def analyze_fleet(fleet_id: str, request: FleetAnalysisRequest):
    """
    Analyze fleet intelligence metrics.
    
    - **fleet_id**: Fleet identifier (path parameter)
    - **metrics**: Specific metrics to analyze (optional)
    """
    try:
        logger.info(f"Fleet analysis request: {fleet_id}")
        analysis = await workflow.analyze_fleet(
            fleet_id=fleet_id,
            metrics=request.metrics
        )
        return FleetAnalysisResponse(
            fleet_id=analysis.fleet_id,
            total_vehicles=analysis.total_vehicles,
            active_vehicles=analysis.active_vehicles,
            utilization_rate=analysis.utilization_rate,
            avg_battery_health=analysis.avg_battery_health,
            maintenance_alerts=analysis.maintenance_alerts,
            key_insights=analysis.key_insights,
            recommendations=analysis.recommendations,
            timestamp=analysis.timestamp
        )
    except Exception as e:
        logger.error(f"Fleet analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze fleet"
        )


@router.get("/vehicle/{vehicle_id}/status", response_model=VehicleStatusResponse)
async def get_vehicle_status(vehicle_id: str):
    """
    Get real-time vehicle status.
    
    - **vehicle_id**: Vehicle identifier (path parameter)
    """
    try:
        logger.info(f"Vehicle status request: {vehicle_id}")
        status_data = await workflow.get_vehicle_status(vehicle_id)
        return VehicleStatusResponse(
            vehicle_id=status_data.vehicle_id,
            vehicle_type=status_data.vehicle_type,
            status=status_data.status,
            battery_level=status_data.battery_level,
            location=status_data.location,
            available=status_data.available,
            last_updated=status_data.last_updated
        )
    except Exception as e:
        logger.error(f"Vehicle status fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch vehicle status"
        )


@router.get("/vehicle/{vehicle_id}/maintenance", response_model=MaintenancePredictionResponse)
async def predict_maintenance(vehicle_id: str):
    """
    Predict maintenance needs for a vehicle.
    
    - **vehicle_id**: Vehicle identifier (path parameter)
    """
    try:
        logger.info(f"Maintenance prediction request: {vehicle_id}")
        prediction = await workflow.predict_maintenance(vehicle_id)
        return MaintenancePredictionResponse(
            vehicle_id=prediction.vehicle_id,
            maintenance_needed=prediction.maintenance_needed,
            priority=prediction.priority,
            predicted_failure_component=prediction.predicted_failure_component,
            recommended_action=prediction.recommended_action,
            days_until_maintenance=prediction.days_until_maintenance,
            timestamp=prediction.timestamp
        )
    except Exception as e:
        logger.error(f"Maintenance prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict maintenance"
        )


@router.post("/fleet/{fleet_id}/optimize-distribution", response_model=FleetDistributionResponse)
async def optimize_fleet_distribution(fleet_id: str, request: FleetDistributionRequest):
    """
    Optimize vehicle distribution across target locations.
    
    - **fleet_id**: Fleet identifier (path parameter)
    - **target_locations**: Locations that need vehicles
    """
    try:
        logger.info(f"Fleet distribution optimization: {fleet_id}")
        distribution = await workflow.optimize_fleet_distribution(
            fleet_id=fleet_id,
            target_locations=request.target_locations
        )
        return FleetDistributionResponse(
            fleet_id=distribution["fleet_id"],
            timestamp=distribution["timestamp"],
            current_state=distribution["current_state"],
            demand_forecast=distribution["demand_forecast"],
            recommendations=distribution["recommendations"]
        )
    except Exception as e:
        logger.error(f"Fleet distribution optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize fleet distribution"
        )


@router.post(
    "/destination/intelligent",
    response_model=IntelligentDestinationResponse,
)
async def intelligent_destination(request: IntelligentDestinationRequest):
    """
    Compute smart destination recommendation with backend AOQ decisioning.

    - **query**: Destination typed by user
    - **candidate_destinations**: Optional destination candidates
    - **trip_history**: Optional destination history with usage count
    - **travel_mode**: solo, family, or eco
    """
    try:
        logger.info(
            "event=mobility_destination_intelligence_requested user_id=%s origin=%s query=%s",
            request.user_id,
            request.origin,
            request.query,
        )
        result = destination_workflow.evaluate(
            user_id=request.user_id,
            origin=request.origin,
            query=request.query,
            candidate_destinations=request.candidate_destinations,
            trip_history=request.trip_history,
            travel_mode=request.travel_mode,
            traffic_level=request.traffic_level,
            weather_risk=request.weather_risk,
            battery_level=request.battery_level,
            is_recurring=request.is_recurring,
            hour_of_day=request.hour_of_day,
        )
        return IntelligentDestinationResponse(
            selected_destination=result.selected_destination,
            confidence=result.confidence,
            alternatives=[
                IntelligentDestinationAlternative(
                    destination=item.destination,
                    confidence=item.confidence,
                    score=item.score,
                )
                for item in result.alternatives
            ],
            aoq=IntelligentDestinationAoq(
                mobility_score=result.aoq.mobility_score,
                esg_score=result.aoq.esg_score,
                dispatch_recommendation=result.aoq.dispatch_recommendation,
                decision=result.aoq.decision,
                rationale=result.aoq.rationale,
            ),
            simulation=IntelligentDestinationSimulation(
                route_id=result.simulation.route_id,
                distance_km=result.simulation.distance_km,
                estimated_time_minutes=result.simulation.estimated_time_minutes,
                estimated_price_xof=result.simulation.estimated_price_xof,
                energy_kwh=result.simulation.energy_kwh,
                co2_saved_kg=result.simulation.co2_saved_kg,
            ),
            timestamp=result.timestamp,
        )
    except MobilityDestinationValidationError as exc:
        logger.warning(
            "event=mobility_destination_intelligence_validation_failed user_id=%s reason=%s",
            request.user_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "event=mobility_destination_intelligence_error user_id=%s error=%s",
            request.user_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute intelligent destination",
        ) from exc


def _require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MOBILITY_IDEMPOTENCY_REQUIRED",
                "message": "Idempotency-Key header required",
                "details": {},
            },
        )
    return idempotency_key


def _raise_lifecycle_error(exc: RideLifecycleError) -> None:
    raise HTTPException(
        status_code=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
        detail={
            "code": getattr(exc, "code", "MOBILITY_RIDE_ERROR"),
            "message": str(exc),
            "details": getattr(exc, "details", {}),
        },
    ) from exc


async def _publish_event(topic: str, key: str, payload: dict) -> None:
    try:
        event_bus = await get_event_bus()
        await event_bus.publish_raw(topic=topic, key=key, payload=payload)
    except Exception as exc:
        logger.warning(
            "event=mobility_event_publish_failed topic=%s key=%s reason=%s",
            topic,
            key,
            str(exc),
        )


@router.post("/ride/quote", response_model=RideQuoteResponse)
async def quote_ride(
    payload: RideQuoteRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    key = _require_idempotency_key(idempotency_key)
    try:
        quote = ride_lifecycle_service.quote_ride(
            rider_id=payload.rider_id,
            pickup_label=payload.pickup_label,
            dropoff_label=payload.dropoff_label,
            service_tier=payload.service_tier,
            idempotency_key=key,
        )
        await _publish_event(
            topic="ride.quote.requested",
            key=quote["quote_id"],
            payload={
                "quote_id": quote["quote_id"],
                "rider_id": quote["rider_id"],
                "correlation_id": request.headers.get("X-Correlation-ID"),
            },
        )
        return RideQuoteResponse.model_validate(quote)
    except RideLifecycleError as exc:
        _raise_lifecycle_error(exc)


@router.post("/ride/book", response_model=RideStateResponse)
async def book_ride(
    payload: RideBookRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    key = _require_idempotency_key(idempotency_key)
    try:
        ride = ride_lifecycle_service.book_ride(
            quote_id=payload.quote_id,
            rider_id=payload.rider_id,
            idempotency_key=key,
        )
        await _publish_event(
            topic="ride.created",
            key=ride["ride_id"],
            payload={
                "ride_id": ride["ride_id"],
                "rider_id": ride["rider_id"],
                "correlation_id": request.headers.get("X-Correlation-ID"),
            },
        )
        return RideStateResponse.model_validate(ride)
    except RideLifecycleError as exc:
        _raise_lifecycle_error(exc)


@router.post("/ride/assign", response_model=RideStateResponse)
async def assign_ride(
    payload: RideAssignRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    key = _require_idempotency_key(idempotency_key)
    try:
        ride = ride_lifecycle_service.assign_ride(
            ride_id=payload.ride_id,
            driver_id=payload.driver_id,
            idempotency_key=key,
        )
        await _publish_event(
            topic="ride.assigned",
            key=ride["ride_id"],
            payload={
                "ride_id": ride["ride_id"],
                "driver_id": ride["driver_id"],
                "correlation_id": request.headers.get("X-Correlation-ID"),
            },
        )
        return RideStateResponse.model_validate(ride)
    except RideLifecycleError as exc:
        _raise_lifecycle_error(exc)


@router.post("/ride/cancel", response_model=RideStateResponse)
async def cancel_ride(
    payload: RideCancelRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    key = _require_idempotency_key(idempotency_key)
    try:
        ride = ride_lifecycle_service.cancel_ride(
            ride_id=payload.ride_id,
            reason=payload.reason,
            idempotency_key=key,
        )
        return RideStateResponse.model_validate(ride)
    except RideLifecycleError as exc:
        _raise_lifecycle_error(exc)


@router.post("/ride/complete", response_model=RideStateResponse)
async def complete_ride(
    payload: RideCompleteRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    key = _require_idempotency_key(idempotency_key)
    try:
        ride = ride_lifecycle_service.complete_ride(
            ride_id=payload.ride_id,
            distance_km=payload.distance_km,
            duration_minutes=payload.duration_minutes,
            idempotency_key=key,
        )
        await _publish_event(
            topic="ride.completed",
            key=ride["ride_id"],
            payload={
                "ride_id": ride["ride_id"],
                "rider_id": ride["rider_id"],
                "final_price_xof": ride["final_price_xof"],
                "correlation_id": request.headers.get("X-Correlation-ID"),
            },
        )
        return RideStateResponse.model_validate(ride)
    except RideLifecycleError as exc:
        _raise_lifecycle_error(exc)


@router.get("/ride/{ride_id}", response_model=RideStateResponse)
async def get_ride(ride_id: str):
    try:
        ride = ride_lifecycle_service.get_ride(ride_id=ride_id)
        return RideStateResponse.model_validate(ride)
    except RideLifecycleError as exc:
        _raise_lifecycle_error(exc)
