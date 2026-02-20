"""
ESG Scoring Workflow for Health & Sustainability Operations.

Orchestrates pedometer data processing, health profile analysis, ESG scoring,
and institutional reporting. Coordinates between beryl-core-api and berylcommunity-wb.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
from src.adapters.esg_community_wb.client import EsgCommunityClient
from src.adapters.esg_community_wb.mapper import (
    EsgMapper,
    PedometerData,
    HealthProfile,
    EsgScore,
    SustainabilityIndicators,
    CommunityImpact,
    HealthChallenge,
    WellbeingScore,
    EsgReport
)
from src.observability.logger import logger


class EsgScoringWorkflow:
    """Orchestrates ESG and health data operations."""

    def __init__(self):
        self.client = EsgCommunityClient()
        self.mapper = EsgMapper()

    async def get_pedometer_data(
        self,
        user_id: str,
        date_from: date,
        date_to: date
    ) -> PedometerData:
        """
        Retrieve and normalize pedometer data.
        
        Workflow:
        1. Call berylcommunity-wb pedometer API
        2. Map response to internal PedometerData model
        3. Validate step counts and metrics
        
        Args:
            user_id: User identifier
            date_from: Start date
            date_to: End date
            
        Returns:
            Normalized PedometerData
        """
        logger.info(f"Fetching pedometer data for user: {user_id}")
        
        raw_response = await self.client.get_pedometer_data(user_id, date_from, date_to)
        data = self.mapper.map_pedometer_response(raw_response)
        
        logger.info(f"Pedometer data retrieved: {data.steps} steps, {data.distance_km}km")
        return data

    async def get_health_profile(
        self,
        user_id: str
    ) -> HealthProfile:
        """
        Retrieve and normalize health profile - SENSITIVE DATA.
        
        Workflow:
        1. Call berylcommunity-wb health API
        2. Map response to internal HealthProfile model
        3. Anonymize/bin sensitive health data
        
        Args:
            user_id: User identifier
            
        Returns:
            Normalized HealthProfile with privacy protections
        """
        logger.info(f"Fetching health profile for user: {user_id}")
        
        raw_response = await self.client.get_health_profile(user_id)
        profile = self.mapper.map_health_profile_response(raw_response)
        
        logger.info(f"Health profile retrieved: health_score={profile.health_score}")
        return profile

    async def calculate_esg_score(
        self,
        user_id: str,
        period: str = "monthly"
    ) -> EsgScore:
        """
        Calculate ESG score for user.
        
        Workflow:
        1. Call berylcommunity-wb ESG calculation API
        2. Map response to internal EsgScore model
        3. Extract trend information
        
        Args:
            user_id: User identifier
            period: Calculation period
            
        Returns:
            Normalized EsgScore with component breakdown
        """
        logger.info(f"Calculating ESG score for user: {user_id}, period: {period}")
        
        raw_response = await self.client.calculate_esg_score(user_id, period)
        score = self.mapper.map_esg_score_response(raw_response)
        
        logger.info(
            f"ESG score calculated: E={score.environmental_score} "
            f"S={score.social_score} G={score.governance_score} "
            f"Overall={score.overall_score}"
        )
        return score

    async def get_sustainability_indicators(
        self,
        user_id: str
    ) -> SustainabilityIndicators:
        """
        Get sustainability indicators for user.
        
        Workflow:
        1. Call berylcommunity-wb sustainability API
        2. Map response to internal SustainabilityIndicators model
        3. Calculate carbon impact
        
        Args:
            user_id: User identifier
            
        Returns:
            Normalized SustainabilityIndicators
        """
        logger.info(f"Fetching sustainability indicators for user: {user_id}")
        
        raw_response = await self.client.get_sustainability_indicators(user_id)
        indicators = self.mapper.map_sustainability_response(raw_response)
        
        logger.info(
            f"Sustainability indicators: carbon_footprint={indicators.carbon_footprint_kg}kg, "
            f"green_score={indicators.green_score}, "
            f"sustainable_transport={indicators.sustainable_transport_percent}%"
        )
        return indicators

    async def get_community_impact(
        self,
        community_id: str
    ) -> CommunityImpact:
        """
        Get aggregated community impact metrics.
        
        Workflow:
        1. Call berylcommunity-wb community API
        2. Map response to internal CommunityImpact model
        3. Extract collective metrics
        
        Args:
            community_id: Community identifier
            
        Returns:
            Normalized CommunityImpact
        """
        logger.info(f"Fetching community impact for: {community_id}")
        
        raw_response = await self.client.get_community_impact(community_id)
        impact = self.mapper.map_community_impact_response(raw_response)
        
        logger.info(
            f"Community impact: {impact.total_members} members, "
            f"avg ESG={impact.avg_esg_score}, "
            f"carbon saved={impact.collective_carbon_saved_kg}kg"
        )
        return impact

    async def get_active_challenges(
        self,
        user_id: str
    ) -> List[HealthChallenge]:
        """
        Get active health challenges for user.
        
        Workflow:
        1. Call berylcommunity-wb challenges API
        2. Map each challenge to internal HealthChallenge model
        3. Filter active challenges
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active HealthChallenge models
        """
        logger.info(f"Fetching active challenges for user: {user_id}")
        
        raw_response = await self.client.get_health_challenges(user_id)
        challenges = [
            self.mapper.map_challenge_response(c)
            for c in raw_response.get("challenges", [])
            if c.get("is_active", False)
        ]
        
        logger.info(f"Active challenges found: {len(challenges)}")
        return challenges

    async def get_wellbeing_score(
        self,
        user_id: str
    ) -> WellbeingScore:
        """
        Get comprehensive wellbeing score.
        
        Workflow:
        1. Call berylcommunity-wb wellbeing API
        2. Map response to internal WellbeingScore model
        3. Extract recommendations
        
        Args:
            user_id: User identifier
            
        Returns:
            Normalized WellbeingScore with recommendations
        """
        logger.info(f"Fetching wellbeing score for user: {user_id}")
        
        raw_response = await self.client.get_wellbeing_score(user_id)
        wellbeing = self.mapper.map_wellbeing_response(raw_response)
        
        logger.info(
            f"Wellbeing score: Physical={wellbeing.physical_score} "
            f"Mental={wellbeing.mental_score} Social={wellbeing.social_score} "
            f"Overall={wellbeing.overall_wellbeing}"
        )
        return wellbeing

    async def generate_esg_report(
        self,
        user_id: str,
        report_type: str = "standard"
    ) -> EsgReport:
        """
        Generate ESG report for institutional reporting.
        
        Workflow:
        1. Call berylcommunity-wb report generation API
        2. Map response to internal EsgReport model
        3. Include compliance status and audit trail
        
        Args:
            user_id: User identifier
            report_type: standard, detailed, executive
            
        Returns:
            Normalized EsgReport ready for institutional use
        """
        logger.info(f"Generating {report_type} ESG report for user: {user_id}")
        
        raw_response = await self.client.generate_esg_report(user_id, report_type)
        report = self.mapper.map_esg_report_response(raw_response)
        
        logger.info(
            f"ESG report generated: {report.report_id}, "
            f"compliance_status={report.compliance_status}"
        )
        return report

    async def create_personalized_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create personalized ESG and health insights.
        
        Workflow:
        1. Fetch pedometer data (last 7 days)
        2. Fetch health profile
        3. Calculate ESG score
        4. Get wellbeing score
        5. Combine into personalized insights
        
        Args:
            user_id: User identifier
            
        Returns:
            Personalized insights with actionable recommendations
        """
        logger.info(f"Creating personalized insights for user: {user_id}")
        
        from datetime import timedelta
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        pedometer_data = await self.get_pedometer_data(user_id, week_ago, today)
        health_profile = await self.get_health_profile(user_id)
        esg_score = await self.calculate_esg_score(user_id, "weekly")
        wellbeing = await self.get_wellbeing_score(user_id)
        challenges = await self.get_active_challenges(user_id)
        
        insights = {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "pedometer_summary": {
                "weekly_steps": pedometer_data.steps,
                "distance_km": pedometer_data.distance_km,
                "calories_burned": pedometer_data.calories_burned,
                "active_minutes": pedometer_data.active_minutes
            },
            "health_summary": {
                "health_score": health_profile.health_score,
                "age_range": health_profile.age_range,
                "conditions_count": len(health_profile.medical_conditions)
            },
            "esg_summary": {
                "overall_score": esg_score.overall_score,
                "environmental": esg_score.environmental_score,
                "social": esg_score.social_score,
                "governance": esg_score.governance_score,
                "trend": esg_score.trend
            },
            "wellbeing_summary": {
                "overall": wellbeing.overall_wellbeing,
                "physical": wellbeing.physical_score,
                "mental": wellbeing.mental_score,
                "social": wellbeing.social_score,
                "recommendations": wellbeing.recommendations[:3]  # Top 3
            },
            "active_challenges": len(challenges),
            "next_milestone": None
        }
        
        logger.info(f"Personalized insights created for {user_id}")
        return insights

    async def close(self):
        """Close client connections."""
        await self.client.close()
