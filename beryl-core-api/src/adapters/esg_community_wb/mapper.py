"""
Mapper for ESG Community Wellbeing API.

This module maps data between berylcommunity-wb responses and internal domain models.
Normalizes all external API responses to consistent internal format with special care
for sensitive health and personal data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class PedometerData(BaseModel):
    """Normalized pedometer metrics model."""
    user_id: str
    date: date
    steps: int = Field(..., description="Total steps taken")
    distance_km: float = Field(..., description="Distance walked in km")
    calories_burned: float = Field(..., description="Calories burned")
    active_minutes: int = Field(..., description="Active minutes")
    heart_rate_avg: Optional[float] = Field(None, description="Average heart rate")
    timestamp: datetime


class HealthProfile(BaseModel):
    """Normalized health profile model - SENSITIVE DATA."""
    user_id: str
    age_range: str = Field(..., description="Age range (binned for privacy)")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    blood_pressure: Optional[str] = Field(None, description="BP reading")
    health_score: float = Field(..., description="Overall health score 0-100")
    medical_conditions: List[str] = Field(default_factory=list)
    medications: int = Field(default=0, description="Number of medications")
    last_checkup: Optional[date] = Field(None, description="Last health checkup date")
    timestamp: datetime


class EsgScore(BaseModel):
    """Normalized ESG score model."""
    user_id: str
    environmental_score: float = Field(..., ge=0, le=100)
    social_score: float = Field(..., ge=0, le=100)
    governance_score: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    period: str = Field(..., description="daily, weekly, monthly, yearly")
    trend: str = Field(..., description="up, stable, down")
    timestamp: datetime


class SustainabilityIndicators(BaseModel):
    """Normalized sustainability metrics model."""
    user_id: str
    carbon_footprint_kg: float = Field(..., description="Carbon footprint in kg CO2")
    green_score: float = Field(..., ge=0, le=100, description="Green practices score")
    renewable_energy_percent: float = Field(..., ge=0, le=100)
    waste_reduction_score: float = Field(..., ge=0, le=100)
    sustainable_transport_percent: float = Field(..., ge=0, le=100)
    community_impact_score: float = Field(..., ge=0, le=100)
    timestamp: datetime


class CommunityImpact(BaseModel):
    """Normalized community-level impact model."""
    community_id: str
    total_members: int
    avg_esg_score: float
    collective_carbon_saved_kg: float
    members_active_today: int
    sustainability_initiatives: List[str]
    community_health_rank: str = Field(..., description="percentile ranking")
    timestamp: datetime


class HealthChallenge(BaseModel):
    """Normalized health challenge model."""
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


class WellbeingScore(BaseModel):
    """Normalized comprehensive wellbeing score model."""
    user_id: str
    physical_score: float = Field(..., ge=0, le=100)
    mental_score: float = Field(..., ge=0, le=100)
    social_score: float = Field(..., ge=0, le=100)
    spiritual_score: float = Field(..., ge=0, le=100)
    overall_wellbeing: float = Field(..., ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)
    timestamp: datetime


class EsgReport(BaseModel):
    """Normalized ESG institutional report model."""
    user_id: str
    report_id: str
    report_type: str = Field(..., description="standard, detailed, executive")
    generated_date: datetime
    period_start: date
    period_end: date
    esg_scores: Dict[str, float]
    compliance_status: str = Field(..., description="compliant, review_required, non_compliant")
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    timestamp: datetime


class EsgMapper:
    """Maps berylcommunity-wb API responses to internal domain models."""

    @staticmethod
    def map_pedometer_response(external_response: Dict[str, Any]) -> PedometerData:
        """Map pedometer response to normalized model."""
        return PedometerData(
            user_id=external_response.get("user_id", ""),
            date=datetime.fromisoformat(external_response.get("date", "")).date() 
                 if isinstance(external_response.get("date"), str) else external_response.get("date"),
            steps=int(external_response.get("steps", 0)),
            distance_km=float(external_response.get("distance_km", 0.0)),
            calories_burned=float(external_response.get("calories_burned", 0.0)),
            active_minutes=int(external_response.get("active_minutes", 0)),
            heart_rate_avg=float(external_response.get("heart_rate_avg")) if external_response.get("heart_rate_avg") else None,
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_health_profile_response(external_response: Dict[str, Any]) -> HealthProfile:
        """Map health profile response - SENSITIVE DATA."""
        return HealthProfile(
            user_id=external_response.get("user_id", ""),
            age_range=external_response.get("age_range", "unknown"),
            bmi=float(external_response.get("bmi")) if external_response.get("bmi") else None,
            blood_pressure=external_response.get("blood_pressure"),
            health_score=float(external_response.get("health_score", 0.0)),
            medical_conditions=external_response.get("medical_conditions", []),
            medications=int(external_response.get("medications", 0)),
            last_checkup=datetime.fromisoformat(external_response.get("last_checkup", "")).date()
                        if external_response.get("last_checkup") else None,
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_esg_score_response(external_response: Dict[str, Any]) -> EsgScore:
        """Map ESG score response to normalized model."""
        return EsgScore(
            user_id=external_response.get("user_id", ""),
            environmental_score=float(external_response.get("environmental_score", 0.0)),
            social_score=float(external_response.get("social_score", 0.0)),
            governance_score=float(external_response.get("governance_score", 0.0)),
            overall_score=float(external_response.get("overall_score", 0.0)),
            period=external_response.get("period", "monthly"),
            trend=external_response.get("trend", "stable"),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_sustainability_response(external_response: Dict[str, Any]) -> SustainabilityIndicators:
        """Map sustainability indicators response to normalized model."""
        return SustainabilityIndicators(
            user_id=external_response.get("user_id", ""),
            carbon_footprint_kg=float(external_response.get("carbon_footprint_kg", 0.0)),
            green_score=float(external_response.get("green_score", 0.0)),
            renewable_energy_percent=float(external_response.get("renewable_energy_percent", 0.0)),
            waste_reduction_score=float(external_response.get("waste_reduction_score", 0.0)),
            sustainable_transport_percent=float(external_response.get("sustainable_transport_percent", 0.0)),
            community_impact_score=float(external_response.get("community_impact_score", 0.0)),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_community_impact_response(external_response: Dict[str, Any]) -> CommunityImpact:
        """Map community impact response to normalized model."""
        return CommunityImpact(
            community_id=external_response.get("community_id", ""),
            total_members=int(external_response.get("total_members", 0)),
            avg_esg_score=float(external_response.get("avg_esg_score", 0.0)),
            collective_carbon_saved_kg=float(external_response.get("collective_carbon_saved_kg", 0.0)),
            members_active_today=int(external_response.get("members_active_today", 0)),
            sustainability_initiatives=external_response.get("sustainability_initiatives", []),
            community_health_rank=external_response.get("community_health_rank", "50th"),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_challenge_response(external_response: Dict[str, Any]) -> HealthChallenge:
        """Map health challenge response to normalized model."""
        return HealthChallenge(
            challenge_id=external_response.get("challenge_id", ""),
            user_id=external_response.get("user_id", ""),
            challenge_name=external_response.get("challenge_name", ""),
            description=external_response.get("description", ""),
            progress_percent=float(external_response.get("progress_percent", 0.0)),
            duration_days=int(external_response.get("duration_days", 0)),
            days_remaining=int(external_response.get("days_remaining", 0)),
            reward_points=int(external_response.get("reward_points", 0)),
            difficulty=external_response.get("difficulty", "medium"),
            is_active=external_response.get("is_active", False),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_wellbeing_response(external_response: Dict[str, Any]) -> WellbeingScore:
        """Map wellbeing score response to normalized model."""
        return WellbeingScore(
            user_id=external_response.get("user_id", ""),
            physical_score=float(external_response.get("physical_score", 0.0)),
            mental_score=float(external_response.get("mental_score", 0.0)),
            social_score=float(external_response.get("social_score", 0.0)),
            spiritual_score=float(external_response.get("spiritual_score", 0.0)),
            overall_wellbeing=float(external_response.get("overall_wellbeing", 0.0)),
            recommendations=external_response.get("recommendations", []),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_esg_report_response(external_response: Dict[str, Any]) -> EsgReport:
        """Map ESG report response to normalized model."""
        return EsgReport(
            user_id=external_response.get("user_id", ""),
            report_id=external_response.get("report_id", ""),
            report_type=external_response.get("report_type", "standard"),
            generated_date=datetime.fromisoformat(external_response.get("generated_date", datetime.utcnow().isoformat())),
            period_start=datetime.fromisoformat(external_response.get("period_start", "")).date()
                        if external_response.get("period_start") else date.today(),
            period_end=datetime.fromisoformat(external_response.get("period_end", "")).date()
                      if external_response.get("period_end") else date.today(),
            esg_scores=external_response.get("esg_scores", {}),
            compliance_status=external_response.get("compliance_status", "compliant"),
            audit_trail=external_response.get("audit_trail", []),
            certifications=external_response.get("certifications", []),
            timestamp=datetime.fromisoformat(
                external_response.get("timestamp", datetime.utcnow().isoformat())
            )
        )