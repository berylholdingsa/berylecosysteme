"""Schemas for social network operations."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class PersonalizedFeedRequest(BaseModel):
    """Request for personalized feed."""
    user_id: str = Field(..., description="User identifier")
    limit: int = Field(default=20, description="Number of items")
    offset: int = Field(default=0, description="Pagination offset")


class FeedItemResponse(BaseModel):
    """Response for feed item."""
    item_id: str
    author_id: str
    content_type: str
    content_text: str
    engagement_score: float = Field(..., ge=0, le=100)
    predicted_engagement: float
    rank_score: float
    timestamp_created: datetime


class RecommendationRequest(BaseModel):
    """Request for recommendations."""
    user_id: str = Field(..., description="User identifier")
    recommendation_type: str = Field(default="content", description="content, users, communities")
    limit: int = Field(default=10, description="Number of recommendations")


class RecommendationResponse(BaseModel):
    """Response for recommendation."""
    recommendation_id: str
    target_id: str
    recommendation_type: str
    confidence_score: float = Field(..., ge=0, le=100)
    reason: str
    timestamp: datetime


class BehaviorAnalysisRequest(BaseModel):
    """Request for behavior analysis."""
    user_id: str = Field(..., description="User identifier")
    period_days: int = Field(default=30, description="Analysis period")


class BehaviorAnalysisResponse(BaseModel):
    """Response for behavior analysis."""
    user_id: str
    engagement_level: str
    preferred_content_types: List[str]
    posting_frequency: float
    interaction_patterns: Dict[str, Any]
    peak_activity_hours: List[int]
    community_affinity: List[str]
    timestamp: datetime


class ModerationCheckRequest(BaseModel):
    """Request for content moderation."""
    content_id: str = Field(..., description="Content identifier")
    content_text: str = Field(..., description="Content to check")
    content_type: str = Field(default="post", description="Type of content")


class ModerationCheckResponse(BaseModel):
    """Response for moderation check."""
    content_id: str
    risk_score: float = Field(..., ge=0, le=100)
    violation_types: List[str]
    confidence: float = Field(..., ge=0, le=100)
    recommended_action: str = Field(..., description="allow, review, remove, block")
    timestamp: datetime


class TrendingContentResponse(BaseModel):
    """Response for trending content."""
    content_id: str
    author_id: str
    title: str
    category: str
    trend_score: float = Field(..., ge=0, le=100)
    engagement_count: int
    growth_rate: float
    timestamp: datetime


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis."""
    community_id: str = Field(..., description="Community identifier")
    period_days: int = Field(default=7, description="Analysis period")


class SentimentAnalysisResponse(BaseModel):
    """Response for sentiment analysis."""
    community_id: str
    overall_sentiment: str = Field(..., description="positive, neutral, negative")
    sentiment_score: float = Field(..., ge=-100, le=100)
    emotion_breakdown: Dict[str, float]
    key_topics: List[str]
    timestamp: datetime


class ConnectionSuggestionResponse(BaseModel):
    """Response for connection suggestion."""
    suggestion_id: str
    user_id: str
    suggested_user_id: str
    relevance_score: float = Field(..., ge=0, le=100)
    common_interests: List[str]
    timestamp: datetime
