"""
Feed Intelligence Workflow for Social Network Operations.

Orchestrates feed generation, behavioral analysis, moderation, and recommendations.
"""

from typing import Dict, List, Any
from datetime import datetime
from src.adapters.social_community_ai.client import SocialAIClient
from src.adapters.social_community_ai.mapper import (
    SocialMapper,
    FeedItem,
    UserRecommendation,
    BehaviorProfile,
    ModerationSignal,
    TrendingContent,
    SentimentAnalysis
)
from src.observability.logger import logger


class FeedIntelligenceWorkflow:
    """Orchestrates social network intelligence operations."""

    def __init__(self):
        self.client = SocialAIClient()
        self.mapper = SocialMapper()

    async def generate_personalized_feed(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[FeedItem]:
        """Generate personalized feed for user."""
        logger.info(f"Generating feed for user: {user_id}")
        
        raw_response = await self.client.generate_personalized_feed(user_id, limit, offset)
        feed_items = [
            self.mapper.map_feed_item(item)
            for item in raw_response.get("items", [])
        ]
        
        logger.info(f"Feed generated: {len(feed_items)} items")
        return feed_items

    async def get_recommendations(
        self,
        user_id: str,
        recommendation_type: str = "content",
        limit: int = 10
    ) -> List[UserRecommendation]:
        """Get AI-powered recommendations."""
        logger.info(f"Fetching {recommendation_type} recommendations for user: {user_id}")
        
        raw_response = await self.client.get_user_recommendations(
            user_id, recommendation_type, limit
        )
        recommendations = [
            self.mapper.map_recommendation(rec)
            for rec in raw_response.get("recommendations", [])
        ]
        
        logger.info(f"Recommendations generated: {len(recommendations)}")
        return recommendations

    async def analyze_user_behavior(
        self,
        user_id: str,
        period_days: int = 30
    ) -> BehaviorProfile:
        """Analyze user behavioral patterns."""
        logger.info(f"Analyzing behavior for user: {user_id}")
        
        raw_response = await self.client.analyze_user_behavior(user_id, period_days)
        profile = self.mapper.map_behavior_profile(raw_response)
        
        logger.info(f"Behavior profile generated: engagement={profile.engagement_level}")
        return profile

    async def check_content_moderation(
        self,
        content_id: str,
        content_text: str,
        content_type: str = "post"
    ) -> ModerationSignal:
        """Check content for moderation signals."""
        logger.info(f"Checking moderation for content: {content_id}")
        
        raw_response = await self.client.check_content_moderation(
            content_id, content_text, content_type
        )
        signal = self.mapper.map_moderation_signal(raw_response)
        
        if signal.risk_score > 50:
            logger.warning(f"High risk content detected: {content_id}, risk={signal.risk_score}")
        
        return signal

    async def get_trending_content(
        self,
        category: str = None,
        limit: int = 20
    ) -> List[TrendingContent]:
        """Get trending content across platform."""
        logger.info(f"Fetching trending content")
        
        raw_response = await self.client.get_trending_content(category, limit)
        trending = [
            self.mapper.map_trending_content(item)
            for item in raw_response.get("trending", [])
        ]
        
        logger.info(f"Trending content retrieved: {len(trending)} items")
        return trending

    async def analyze_community_sentiment(
        self,
        community_id: str,
        period_days: int = 7
    ) -> SentimentAnalysis:
        """Analyze community sentiment."""
        logger.info(f"Analyzing sentiment for community: {community_id}")
        
        raw_response = await self.client.detect_community_sentiment(community_id, period_days)
        sentiment = self.mapper.map_sentiment_analysis(raw_response)
        
        logger.info(f"Community sentiment: {sentiment.overall_sentiment}")
        return sentiment

    async def get_engagement_prediction(
        self,
        content_id: str,
        author_id: str
    ) -> Dict[str, Any]:
        """Predict engagement for content."""
        logger.info(f"Predicting engagement for content: {content_id}")
        
        raw_response = await self.client.predict_engagement(content_id, author_id)
        
        prediction = {
            "content_id": content_id,
            "predicted_likes": raw_response.get("predicted_likes", 0),
            "predicted_shares": raw_response.get("predicted_shares", 0),
            "predicted_comments": raw_response.get("predicted_comments", 0),
            "confidence": raw_response.get("confidence", 0.0)
        }
        
        logger.info(f"Engagement predicted: {prediction}")
        return prediction

    async def suggest_connections(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[UserRecommendation]:
        """Suggest user connections."""
        logger.info(f"Suggesting connections for user: {user_id}")
        
        raw_response = await self.client.suggest_connections(user_id, limit)
        suggestions = [
            self.mapper.map_recommendation(rec)
            for rec in raw_response.get("suggestions", [])
        ]
        
        logger.info(f"Connection suggestions: {len(suggestions)}")
        return suggestions

    async def close(self):
        """Close client connections."""
        await self.client.close()
