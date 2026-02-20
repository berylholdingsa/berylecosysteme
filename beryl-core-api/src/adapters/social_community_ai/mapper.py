"""
Mapper for Social Community AI Engine API.

Maps berylcommunity-ai-engine responses to internal domain models.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    """Normalized feed item model."""
    item_id: str
    author_id: str
    content_type: str
    content_text: str
    engagement_score: float = Field(..., ge=0, le=100)
    timestamp_created: datetime
    predicted_engagement: float
    rank_score: float


class UserRecommendation(BaseModel):
    """Normalized user recommendation model."""
    recommendation_id: str
    target_id: str
    recommendation_type: str
    confidence_score: float = Field(..., ge=0, le=100)
    reason: str
    timestamp: datetime


class BehaviorProfile(BaseModel):
    """Normalized behavioral analysis model."""
    user_id: str
    engagement_level: str
    preferred_content_types: List[str]
    posting_frequency: float
    interaction_patterns: Dict[str, Any]
    peak_activity_hours: List[int]
    community_affinity: List[str]
    timestamp: datetime


class ModerationSignal(BaseModel):
    """Normalized moderation signal model."""
    content_id: str
    risk_score: float = Field(..., ge=0, le=100)
    violation_types: List[str]
    confidence: float = Field(..., ge=0, le=100)
    recommended_action: str
    timestamp: datetime


class TrendingContent(BaseModel):
    """Normalized trending content model."""
    content_id: str
    author_id: str
    title: str
    category: str
    trend_score: float = Field(..., ge=0, le=100)
    engagement_count: int
    growth_rate: float
    timestamp: datetime


class SentimentAnalysis(BaseModel):
    """Normalized sentiment analysis model."""
    community_id: str
    overall_sentiment: str
    sentiment_score: float = Field(..., ge=-100, le=100)
    emotion_breakdown: Dict[str, float]
    key_topics: List[str]
    timestamp: datetime


class SocialMapper:
    """Maps berylcommunity-ai-engine responses to internal models."""

    @staticmethod
    def map_feed_item(response: Dict[str, Any]) -> FeedItem:
        """Map feed item response."""
        return FeedItem(
            item_id=response.get("item_id", ""),
            author_id=response.get("author_id", ""),
            content_type=response.get("content_type", "post"),
            content_text=response.get("content_text", ""),
            engagement_score=float(response.get("engagement_score", 0.0)),
            timestamp_created=datetime.fromisoformat(
                response.get("timestamp_created", datetime.utcnow().isoformat())
            ),
            predicted_engagement=float(response.get("predicted_engagement", 0.0)),
            rank_score=float(response.get("rank_score", 0.0))
        )

    @staticmethod
    def map_recommendation(response: Dict[str, Any]) -> UserRecommendation:
        """Map recommendation response."""
        return UserRecommendation(
            recommendation_id=response.get("recommendation_id", ""),
            target_id=response.get("target_id", ""),
            recommendation_type=response.get("type", "content"),
            confidence_score=float(response.get("confidence", 0.0)),
            reason=response.get("reason", ""),
            timestamp=datetime.fromisoformat(
                response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_behavior_profile(response: Dict[str, Any]) -> BehaviorProfile:
        """Map behavioral analysis response."""
        return BehaviorProfile(
            user_id=response.get("user_id", ""),
            engagement_level=response.get("engagement_level", "medium"),
            preferred_content_types=response.get("preferred_content_types", []),
            posting_frequency=float(response.get("posting_frequency", 0.0)),
            interaction_patterns=response.get("interaction_patterns", {}),
            peak_activity_hours=response.get("peak_activity_hours", []),
            community_affinity=response.get("community_affinity", []),
            timestamp=datetime.fromisoformat(
                response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_moderation_signal(response: Dict[str, Any]) -> ModerationSignal:
        """Map moderation check response."""
        return ModerationSignal(
            content_id=response.get("content_id", ""),
            risk_score=float(response.get("risk_score", 0.0)),
            violation_types=response.get("violation_types", []),
            confidence=float(response.get("confidence", 0.0)),
            recommended_action=response.get("recommended_action", "allow"),
            timestamp=datetime.fromisoformat(
                response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_trending_content(response: Dict[str, Any]) -> TrendingContent:
        """Map trending content response."""
        return TrendingContent(
            content_id=response.get("content_id", ""),
            author_id=response.get("author_id", ""),
            title=response.get("title", ""),
            category=response.get("category", "general"),
            trend_score=float(response.get("trend_score", 0.0)),
            engagement_count=int(response.get("engagement_count", 0)),
            growth_rate=float(response.get("growth_rate", 0.0)),
            timestamp=datetime.fromisoformat(
                response.get("timestamp", datetime.utcnow().isoformat())
            )
        )

    @staticmethod
    def map_sentiment_analysis(response: Dict[str, Any]) -> SentimentAnalysis:
        """Map sentiment analysis response."""
        return SentimentAnalysis(
            community_id=response.get("community_id", ""),
            overall_sentiment=response.get("overall_sentiment", "neutral"),
            sentiment_score=float(response.get("sentiment_score", 0.0)),
            emotion_breakdown=response.get("emotion_breakdown", {}),
            key_topics=response.get("key_topics", []),
            timestamp=datetime.fromisoformat(
                response.get("timestamp", datetime.utcnow().isoformat())
            )
        )
