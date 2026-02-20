"""Social network routes for Beryl Core API."""

from fastapi import APIRouter, HTTPException, status, Security
from fastapi.security import HTTPBearer
from src.orchestration.social.feed_intelligence import FeedIntelligenceWorkflow
from src.api.v1.schemas.social_schema import (
    PersonalizedFeedRequest, FeedItemResponse,
    RecommendationRequest, RecommendationResponse,
    BehaviorAnalysisRequest, BehaviorAnalysisResponse,
    ModerationCheckRequest, ModerationCheckResponse,
    TrendingContentResponse,
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    ConnectionSuggestionResponse
)
from src.observability.logger import logger

router = APIRouter()
workflow = FeedIntelligenceWorkflow()
security = HTTPBearer()


@router.post("/feed/personalized", response_model=list[FeedItemResponse], dependencies=[Security(security)])
async def get_personalized_feed(request: PersonalizedFeedRequest):
    """Get personalized feed for user."""
    try:
        logger.info(f"Feed request for user: {request.user_id}")
        feed_items = await workflow.generate_personalized_feed(
            user_id=request.user_id,
            limit=request.limit,
            offset=request.offset
        )
        return [
            FeedItemResponse(
                item_id=item.item_id,
                author_id=item.author_id,
                content_type=item.content_type,
                content_text=item.content_text,
                engagement_score=item.engagement_score,
                predicted_engagement=item.predicted_engagement,
                rank_score=item.rank_score,
                timestamp_created=item.timestamp_created
            )
            for item in feed_items
        ]
    except Exception as e:
        logger.error(f"Feed generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate feed")


@router.post("/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(request: RecommendationRequest):
    """Get AI recommendations for user."""
    try:
        logger.info(f"Recommendations request for user: {request.user_id}")
        recommendations = await workflow.get_recommendations(
            user_id=request.user_id,
            recommendation_type=request.recommendation_type,
            limit=request.limit
        )
        return [
            RecommendationResponse(
                recommendation_id=rec.recommendation_id,
                target_id=rec.target_id,
                recommendation_type=rec.recommendation_type,
                confidence_score=rec.confidence_score,
                reason=rec.reason,
                timestamp=rec.timestamp
            )
            for rec in recommendations
        ]
    except Exception as e:
        logger.error(f"Recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.post("/behavior/analyze", response_model=BehaviorAnalysisResponse)
async def analyze_behavior(request: BehaviorAnalysisRequest):
    """Analyze user behavior patterns."""
    try:
        logger.info(f"Behavior analysis for user: {request.user_id}")
        profile = await workflow.analyze_user_behavior(
            user_id=request.user_id,
            period_days=request.period_days
        )
        return BehaviorAnalysisResponse(
            user_id=profile.user_id,
            engagement_level=profile.engagement_level,
            preferred_content_types=profile.preferred_content_types,
            posting_frequency=profile.posting_frequency,
            interaction_patterns=profile.interaction_patterns,
            peak_activity_hours=profile.peak_activity_hours,
            community_affinity=profile.community_affinity,
            timestamp=profile.timestamp
        )
    except Exception as e:
        logger.error(f"Behavior analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze behavior")


@router.post("/moderation/check", response_model=ModerationCheckResponse)
async def check_moderation(request: ModerationCheckRequest):
    """Check content for moderation flags."""
    try:
        logger.info(f"Moderation check for content: {request.content_id}")
        signal = await workflow.check_content_moderation(
            content_id=request.content_id,
            content_text=request.content_text,
            content_type=request.content_type
        )
        return ModerationCheckResponse(
            content_id=signal.content_id,
            risk_score=signal.risk_score,
            violation_types=signal.violation_types,
            confidence=signal.confidence,
            recommended_action=signal.recommended_action,
            timestamp=signal.timestamp
        )
    except Exception as e:
        logger.error(f"Moderation check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check moderation")


@router.get("/trending", response_model=list[TrendingContentResponse])
async def get_trending(category: str = None, limit: int = 20):
    """Get trending content."""
    try:
        logger.info(f"Fetching trending content")
        trending = await workflow.get_trending_content(category, limit)
        return [
            TrendingContentResponse(
                content_id=t.content_id,
                author_id=t.author_id,
                title=t.title,
                category=t.category,
                trend_score=t.trend_score,
                engagement_count=t.engagement_count,
                growth_rate=t.growth_rate,
                timestamp=t.timestamp
            )
            for t in trending
        ]
    except Exception as e:
        logger.error(f"Trending fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending")


@router.post("/sentiment/community", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """Analyze community sentiment."""
    try:
        logger.info(f"Sentiment analysis for community: {request.community_id}")
        sentiment = await workflow.analyze_community_sentiment(
            community_id=request.community_id,
            period_days=request.period_days
        )
        return SentimentAnalysisResponse(
            community_id=sentiment.community_id,
            overall_sentiment=sentiment.overall_sentiment,
            sentiment_score=sentiment.sentiment_score,
            emotion_breakdown=sentiment.emotion_breakdown,
            key_topics=sentiment.key_topics,
            timestamp=sentiment.timestamp
        )
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze sentiment")


@router.get("/connections/suggest/{user_id}", response_model=list[ConnectionSuggestionResponse])
async def suggest_connections(user_id: str, limit: int = 10):
    """Suggest user connections."""
    try:
        logger.info(f"Suggesting connections for user: {user_id}")
        suggestions = await workflow.suggest_connections(user_id, limit)
        return [
            ConnectionSuggestionResponse(
                suggestion_id=f"sugg_{i}",
                user_id=user_id,
                suggested_user_id=rec.target_id,
                relevance_score=rec.confidence_score,
                common_interests=[],
                timestamp=rec.timestamp
            )
            for i, rec in enumerate(suggestions)
        ]
    except Exception as e:
        logger.error(f"Connection suggestions failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to suggest connections")
