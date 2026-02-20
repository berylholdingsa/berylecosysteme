"""
Schemas for ESG and health operations.

This module defines Pydantic models for ESG, health, and sustainability API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime, date


class PedometerRequest(BaseModel):
    """Request model for pedometer data retrieval."""
    user_id: str = Field(..., description="User identifier")
    date_from: date = Field(..., description="Start date for data retrieval")
    date_to: date = Field(..., description="End date for data retrieval")


class PedometerResponse(BaseModel):
    """Response model for pedometer data."""
    user_id: str
    date: date
    steps: int
    distance_km: float
    calories_burned: float
    active_minutes: int
    heart_rate_avg: Optional[float]
    timestamp: datetime


class HealthProfileRequest(BaseModel):
    """Request model for health profile retrieval."""
    user_id: str = Field(..., description="User identifier")


class HealthProfileResponse(BaseModel):
    """Response model for health profile - SENSITIVE DATA."""
    user_id: str
    age_range: str
    bmi: Optional[float]
    blood_pressure: Optional[str]
    health_score: float = Field(..., ge=0, le=100)
    medical_conditions: List[str]
    medications: int
    last_checkup: Optional[date]
    timestamp: datetime


class EsgScoreRequest(BaseModel):
    """Request model for ESG score calculation."""
    user_id: str = Field(..., description="User identifier")
    period: str = Field(default="monthly", description="daily, weekly, monthly, yearly")


class EsgScoreResponse(BaseModel):
    """Response model for ESG score."""
    user_id: str
    environmental_score: float = Field(..., ge=0, le=100)
    social_score: float = Field(..., ge=0, le=100)
    governance_score: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    period: str
    trend: str = Field(..., description="up, stable, down")
    timestamp: datetime


class SustainabilityIndicatorsRequest(BaseModel):
    """Request model for sustainability indicators."""
    user_id: str = Field(..., description="User identifier")


class SustainabilityIndicatorsResponse(BaseModel):
    """Response model for sustainability indicators."""
    user_id: str
    carbon_footprint_kg: float
    green_score: float = Field(..., ge=0, le=100)
    renewable_energy_percent: float = Field(..., ge=0, le=100)
    waste_reduction_score: float = Field(..., ge=0, le=100)
    sustainable_transport_percent: float = Field(..., ge=0, le=100)
    community_impact_score: float = Field(..., ge=0, le=100)
    timestamp: datetime


class CommunityImpactRequest(BaseModel):
    """Request model for community impact metrics."""
    community_id: str = Field(..., description="Community identifier")


class CommunityImpactResponse(BaseModel):
    """Response model for community impact."""
    community_id: str
    total_members: int
    avg_esg_score: float = Field(..., ge=0, le=100)
    collective_carbon_saved_kg: float
    members_active_today: int
    sustainability_initiatives: List[str]
    community_health_rank: str
    timestamp: datetime


class HealthChallengeResponse(BaseModel):
    """Response model for health challenges."""
    challenge_id: str
    user_id: str
    challenge_name: str
    description: str
    progress_percent: float = Field(..., ge=0, le=100)
    duration_days: int
    days_remaining: int
    reward_points: int
    difficulty: str = Field(..., description="easy, medium, hard")
    is_active: bool
    timestamp: datetime


class WellbeingScoreRequest(BaseModel):
    """Request model for wellbeing score."""
    user_id: str = Field(..., description="User identifier")


class WellbeingScoreResponse(BaseModel):
    """Response model for wellbeing score."""
    user_id: str
    physical_score: float = Field(..., ge=0, le=100)
    mental_score: float = Field(..., ge=0, le=100)
    social_score: float = Field(..., ge=0, le=100)
    spiritual_score: float = Field(..., ge=0, le=100)
    overall_wellbeing: float = Field(..., ge=0, le=100)
    recommendations: List[str]
    timestamp: datetime


class EsgReportRequest(BaseModel):
    """Request model for ESG report generation."""
    user_id: str = Field(..., description="User identifier")
    report_type: str = Field(default="standard", description="standard, detailed, executive")


class EsgReportResponse(BaseModel):
    """Response model for ESG institutional report."""
    user_id: str
    report_id: str
    report_type: str
    generated_date: datetime
    period_start: date
    period_end: date
    esg_scores: Dict[str, float]
    compliance_status: str = Field(..., description="compliant, review_required, non_compliant")
    audit_trail: List[Dict[str, Any]]
    certifications: List[str]
    timestamp: datetime


class PersonalizedInsightsResponse(BaseModel):
    """Response model for personalized ESG and health insights."""
    user_id: str
    generated_at: datetime
    pedometer_summary: Dict[str, Any]
    health_summary: Dict[str, Any]
    esg_summary: Dict[str, Any]
    wellbeing_summary: Dict[str, Any]
    active_challenges: int
    next_milestone: Optional[str]


class EsgScoreComputeRequest(BaseModel):
    """Contract-first backend ESG compute input."""

    user_id: str = Field(..., min_length=1, max_length=128)
    period: Literal["daily", "weekly", "monthly", "yearly"] = "monthly"
    city: Optional[str] = Field(default=None, min_length=2, max_length=128)
    profile: Optional[str] = Field(default=None, min_length=1, max_length=64)
    co2_avoided_kg: Optional[float] = Field(default=None, ge=0)
    green_distance_km: Optional[float] = Field(default=None, ge=0)
    rides_count: Optional[int] = Field(default=None, ge=0)


class EsgScoreComputeResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    class_: Literal["A", "B", "C", "D"] = Field(
        serialization_alias="class",
        validation_alias="class",
    )
    co2_avoided_kg: float = Field(..., ge=0)
    green_distance_km: float = Field(..., ge=0)
    rides_count: int = Field(..., ge=0)
    score_components: Dict[str, float]
    model_version: str
    calculation_hash: str
    confidence_interval: Dict[str, float]


class EsgImpactNormalizeRequest(BaseModel):
    co2_avoided_kg: float = Field(..., ge=0)
    green_distance_km: float = Field(..., ge=0)
    rides_count: int = Field(..., ge=0)
    period: Literal["daily", "weekly", "monthly", "yearly"] = "monthly"


class EsgImpactNormalizeResponse(BaseModel):
    normalized_components: Dict[str, float]
    model_version: str
    calculation_hash: str
