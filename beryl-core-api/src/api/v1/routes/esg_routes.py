"""
ESG routes for the Beryl Core API.

Exposes REST endpoints for ESG, health, and sustainability operations.
Routes orchestrate requests through the ESG scoring workflow.
"""

import hashlib
import json

from fastapi import APIRouter, HTTPException, Header, Request, Security, status
from fastapi.security import HTTPBearer
from src.orchestration.esg.esg_scoring import EsgScoringWorkflow
from src.api.v1.schemas.esg_schema import (
    PedometerRequest, PedometerResponse,
    HealthProfileRequest, HealthProfileResponse,
    EsgScoreRequest, EsgScoreResponse,
    SustainabilityIndicatorsRequest, SustainabilityIndicatorsResponse,
    CommunityImpactRequest, CommunityImpactResponse,
    HealthChallengeResponse,
    WellbeingScoreRequest, WellbeingScoreResponse,
    EsgReportRequest, EsgReportResponse,
    PersonalizedInsightsResponse,
    EsgScoreComputeRequest, EsgScoreComputeResponse,
    EsgImpactNormalizeRequest, EsgImpactNormalizeResponse,
)
from src.events.bus.event_bus import get_event_bus
from src.observability.logger import logger

router = APIRouter()
workflow = EsgScoringWorkflow()
security = HTTPBearer()


@router.post("/pedometer/data", response_model=PedometerResponse, dependencies=[Security(security)])
async def get_pedometer_data(request: PedometerRequest):
    """
    Retrieve pedometer data for a user.
    
    - **user_id**: User identifier
    - **date_from**: Start date for data retrieval
    - **date_to**: End date for data retrieval
    """
    try:
        logger.info(f"Pedometer data request for user: {request.user_id}")
        data = await workflow.get_pedometer_data(
            user_id=request.user_id,
            date_from=request.date_from,
            date_to=request.date_to
        )
        return PedometerResponse(
            user_id=data.user_id,
            date=data.date,
            steps=data.steps,
            distance_km=data.distance_km,
            calories_burned=data.calories_burned,
            active_minutes=data.active_minutes,
            heart_rate_avg=data.heart_rate_avg,
            timestamp=data.timestamp
        )
    except Exception as e:
        logger.error(f"Pedometer data fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pedometer data"
        )


@router.post("/health/profile", response_model=HealthProfileResponse)
async def get_health_profile(request: HealthProfileRequest):
    """
    Retrieve health profile - SENSITIVE DATA.
    
    - **user_id**: User identifier
    """
    try:
        logger.info(f"Health profile request for user: {request.user_id}")
        profile = await workflow.get_health_profile(request.user_id)
        return HealthProfileResponse(
            user_id=profile.user_id,
            age_range=profile.age_range,
            bmi=profile.bmi,
            blood_pressure=profile.blood_pressure,
            health_score=profile.health_score,
            medical_conditions=profile.medical_conditions,
            medications=profile.medications,
            last_checkup=profile.last_checkup,
            timestamp=profile.timestamp
        )
    except Exception as e:
        logger.error(f"Health profile fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch health profile"
        )


@router.post("/esg/score", response_model=EsgScoreResponse)
async def calculate_esg_score(request: EsgScoreRequest):
    """
    Calculate ESG score for a user.
    
    - **user_id**: User identifier
    - **period**: Calculation period (daily, weekly, monthly, yearly)
    """
    try:
        logger.info(f"ESG score calculation for user: {request.user_id}")
        score = await workflow.calculate_esg_score(
            user_id=request.user_id,
            period=request.period
        )
        return EsgScoreResponse(
            user_id=score.user_id,
            environmental_score=score.environmental_score,
            social_score=score.social_score,
            governance_score=score.governance_score,
            overall_score=score.overall_score,
            period=score.period,
            trend=score.trend,
            timestamp=score.timestamp
        )
    except Exception as e:
        logger.error(f"ESG score calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate ESG score"
        )


@router.post("/sustainability/indicators", response_model=SustainabilityIndicatorsResponse)
async def get_sustainability_indicators(request: SustainabilityIndicatorsRequest):
    """
    Get sustainability indicators for a user.
    
    - **user_id**: User identifier
    """
    try:
        logger.info(f"Sustainability indicators request for user: {request.user_id}")
        indicators = await workflow.get_sustainability_indicators(request.user_id)
        return SustainabilityIndicatorsResponse(
            user_id=indicators.user_id,
            carbon_footprint_kg=indicators.carbon_footprint_kg,
            green_score=indicators.green_score,
            renewable_energy_percent=indicators.renewable_energy_percent,
            waste_reduction_score=indicators.waste_reduction_score,
            sustainable_transport_percent=indicators.sustainable_transport_percent,
            community_impact_score=indicators.community_impact_score,
            timestamp=indicators.timestamp
        )
    except Exception as e:
        logger.error(f"Sustainability indicators fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sustainability indicators"
        )


@router.post("/community/{community_id}/impact", response_model=CommunityImpactResponse)
async def get_community_impact(community_id: str, request: CommunityImpactRequest):
    """
    Get community impact metrics.
    
    - **community_id**: Community identifier (path parameter)
    """
    try:
        logger.info(f"Community impact request for: {community_id}")
        impact = await workflow.get_community_impact(community_id)
        return CommunityImpactResponse(
            community_id=impact.community_id,
            total_members=impact.total_members,
            avg_esg_score=impact.avg_esg_score,
            collective_carbon_saved_kg=impact.collective_carbon_saved_kg,
            members_active_today=impact.members_active_today,
            sustainability_initiatives=impact.sustainability_initiatives,
            community_health_rank=impact.community_health_rank,
            timestamp=impact.timestamp
        )
    except Exception as e:
        logger.error(f"Community impact fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch community impact"
        )


@router.get("/challenges/{user_id}/active", response_model=list[HealthChallengeResponse])
async def get_active_challenges(user_id: str):
    """
    Get active health challenges for a user.
    
    - **user_id**: User identifier (path parameter)
    """
    try:
        logger.info(f"Active challenges request for user: {user_id}")
        challenges = await workflow.get_active_challenges(user_id)
        return [
            HealthChallengeResponse(
                challenge_id=c.challenge_id,
                user_id=c.user_id,
                challenge_name=c.challenge_name,
                description=c.description,
                progress_percent=c.progress_percent,
                duration_days=c.duration_days,
                days_remaining=c.days_remaining,
                reward_points=c.reward_points,
                difficulty=c.difficulty,
                is_active=c.is_active,
                timestamp=c.timestamp
            )
            for c in challenges
        ]
    except Exception as e:
        logger.error(f"Active challenges fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active challenges"
        )


@router.post("/wellbeing/score", response_model=WellbeingScoreResponse)
async def get_wellbeing_score(request: WellbeingScoreRequest):
    """
    Get comprehensive wellbeing score for a user.
    
    - **user_id**: User identifier
    """
    try:
        logger.info(f"Wellbeing score request for user: {request.user_id}")
        wellbeing = await workflow.get_wellbeing_score(request.user_id)
        return WellbeingScoreResponse(
            user_id=wellbeing.user_id,
            physical_score=wellbeing.physical_score,
            mental_score=wellbeing.mental_score,
            social_score=wellbeing.social_score,
            spiritual_score=wellbeing.spiritual_score,
            overall_wellbeing=wellbeing.overall_wellbeing,
            recommendations=wellbeing.recommendations,
            timestamp=wellbeing.timestamp
        )
    except Exception as e:
        logger.error(f"Wellbeing score fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch wellbeing score"
        )


@router.post("/reporting/esg-report", response_model=EsgReportResponse)
async def generate_esg_report(request: EsgReportRequest):
    """
    Generate ESG report for institutional reporting.
    
    - **user_id**: User identifier
    - **report_type**: Report type (standard, detailed, executive)
    """
    try:
        logger.info(f"ESG report generation for user: {request.user_id}")
        report = await workflow.generate_esg_report(
            user_id=request.user_id,
            report_type=request.report_type
        )
        return EsgReportResponse(
            user_id=report.user_id,
            report_id=report.report_id,
            report_type=report.report_type,
            generated_date=report.generated_date,
            period_start=report.period_start,
            period_end=report.period_end,
            esg_scores=report.esg_scores,
            compliance_status=report.compliance_status,
            audit_trail=report.audit_trail,
            certifications=report.certifications,
            timestamp=report.timestamp
        )
    except Exception as e:
        logger.error(f"ESG report generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate ESG report"
        )


@router.get("/insights/{user_id}/personalized", response_model=PersonalizedInsightsResponse)
async def get_personalized_insights(user_id: str):
    """
    Get personalized ESG and health insights.
    
    - **user_id**: User identifier (path parameter)
    
    Aggregates pedometer, health, ESG, and wellbeing data for comprehensive view.
    """
    try:
        logger.info(f"Personalized insights request for user: {user_id}")
        insights = await workflow.create_personalized_insights(user_id)
        return PersonalizedInsightsResponse(
            user_id=insights["user_id"],
            generated_at=insights["generated_at"],
            pedometer_summary=insights["pedometer_summary"],
            health_summary=insights["health_summary"],
            esg_summary=insights["esg_summary"],
            wellbeing_summary=insights["wellbeing_summary"],
            active_challenges=insights["active_challenges"],
            next_milestone=insights.get("next_milestone")
        )
    except Exception as e:
        logger.error(f"Personalized insights generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate personalized insights"
        )


_ESG_MODEL_VERSION = "esg-v2.0.0"
_PERIOD_FACTORS = {
    "daily": 0.62,
    "weekly": 0.70,
    "monthly": 0.78,
    "yearly": 0.84,
}


def _require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ESG_IDEMPOTENCY_REQUIRED",
                "message": "Idempotency-Key header required",
                "details": {},
            },
        )
    return idempotency_key


def _seeded_defaults(user_id: str, period: str, city: str | None, profile: str | None) -> tuple[float, float, int]:
    seed_input = f"{user_id}:{period}:{city or ''}:{profile or ''}"
    digest = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
    seed = int(digest[:12], 16)
    co2 = round(0.8 + ((seed % 340) / 100.0), 2)
    distance = round(4.0 + ((seed % 900) / 100.0), 2)
    rides = max(1, (seed % 24) + 1)
    return co2, distance, rides


def _normalize_components(co2_avoided_kg: float, green_distance_km: float, rides_count: int, period: str) -> dict[str, float]:
    normalized = {
        "co2_component": round(min(1.0, co2_avoided_kg / 5.0), 4),
        "distance_component": round(min(1.0, green_distance_km / 40.0), 4),
        "rides_component": round(min(1.0, rides_count / 30.0), 4),
        "period_component": _PERIOD_FACTORS.get(period, _PERIOD_FACTORS["monthly"]),
    }
    return normalized


def _hash_payload(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def _publish_esg_score_event(
    *,
    user_id: str,
    score: int,
    correlation_id: str | None,
    calculation_hash: str,
) -> None:
    try:
        event_bus = await get_event_bus()
        await event_bus.publish_raw(
            topic="esg.score.computed",
            key=user_id,
            payload={
                "user_id": user_id,
                "score": score,
                "calculation_hash": calculation_hash,
                "correlation_id": correlation_id,
            },
        )
    except Exception as exc:
        logger.warning("event=esg_score_event_publish_failed reason=%s", str(exc))


@router.post("/score/compute", response_model=EsgScoreComputeResponse)
async def compute_esg_score(
    payload: EsgScoreComputeRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _require_idempotency_key(idempotency_key)
    co2_default, distance_default, rides_default = _seeded_defaults(
        user_id=payload.user_id,
        period=payload.period,
        city=payload.city,
        profile=payload.profile,
    )
    co2_avoided_kg = payload.co2_avoided_kg if payload.co2_avoided_kg is not None else co2_default
    green_distance_km = payload.green_distance_km if payload.green_distance_km is not None else distance_default
    rides_count = payload.rides_count if payload.rides_count is not None else rides_default

    normalized = _normalize_components(
        co2_avoided_kg=co2_avoided_kg,
        green_distance_km=green_distance_km,
        rides_count=rides_count,
        period=payload.period,
    )
    weighted_score = (
        normalized["co2_component"] * 0.45
        + normalized["distance_component"] * 0.25
        + normalized["rides_component"] * 0.20
        + normalized["period_component"] * 0.10
    )
    score = max(0, min(100, int(round(weighted_score * 100))))
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"

    score_components = {
        "co2_component": round(normalized["co2_component"] * 100, 2),
        "distance_component": round(normalized["distance_component"] * 100, 2),
        "rides_component": round(normalized["rides_component"] * 100, 2),
        "period_component": round(normalized["period_component"] * 100, 2),
    }
    confidence_margin = round(max(2.0, score * 0.06), 2)
    confidence_interval = {
        "lower": round(max(0.0, score - confidence_margin), 2),
        "upper": round(min(100.0, score + confidence_margin), 2),
    }
    hash_payload = {
        "user_id": payload.user_id,
        "period": payload.period,
        "city": payload.city,
        "profile": payload.profile,
        "co2_avoided_kg": co2_avoided_kg,
        "green_distance_km": green_distance_km,
        "rides_count": rides_count,
        "score": score,
        "components": score_components,
        "model_version": _ESG_MODEL_VERSION,
    }
    calculation_hash = _hash_payload(hash_payload)

    await _publish_esg_score_event(
        user_id=payload.user_id,
        score=score,
        correlation_id=request.headers.get("X-Correlation-ID"),
        calculation_hash=calculation_hash,
    )

    return EsgScoreComputeResponse(
        score=score,
        class_=grade,
        co2_avoided_kg=co2_avoided_kg,
        green_distance_km=green_distance_km,
        rides_count=rides_count,
        score_components=score_components,
        model_version=_ESG_MODEL_VERSION,
        calculation_hash=calculation_hash,
        confidence_interval=confidence_interval,
    )


@router.post("/impact/normalize", response_model=EsgImpactNormalizeResponse)
async def normalize_esg_impact(
    payload: EsgImpactNormalizeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _require_idempotency_key(idempotency_key)
    normalized = _normalize_components(
        co2_avoided_kg=payload.co2_avoided_kg,
        green_distance_km=payload.green_distance_km,
        rides_count=payload.rides_count,
        period=payload.period,
    )
    hash_payload = {
        "co2_avoided_kg": payload.co2_avoided_kg,
        "green_distance_km": payload.green_distance_km,
        "rides_count": payload.rides_count,
        "period": payload.period,
        "normalized": normalized,
        "model_version": _ESG_MODEL_VERSION,
    }
    calculation_hash = _hash_payload(hash_payload)
    return EsgImpactNormalizeResponse(
        normalized_components=normalized,
        model_version=_ESG_MODEL_VERSION,
        calculation_hash=calculation_hash,
    )
