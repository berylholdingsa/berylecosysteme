"""
GraphQL Type Definitions for Béryl Ecosystem.

Central schema unifying all domains:
- Fintech (wallets, transactions)
- Mobility (rides, fleet)
- ESG (scores, health)
- Social (posts, feed)
"""

import graphene
from datetime import datetime
from typing import Optional, List


# ============================================================================
# SHARED TYPES
# ============================================================================

class User(graphene.ObjectType):
    """Unified user object across all domains."""
    id = graphene.String(required=True, description="User identifier")
    email = graphene.String(required=True)
    full_name = graphene.String()
    created_at = graphene.DateTime()
    is_active = graphene.Boolean(default_value=True)
    avatar_url = graphene.String()
    
    # Domain-specific connections
    wallet = graphene.Field(lambda: Wallet)
    rides = graphene.List(lambda: Ride)
    posts = graphene.List(lambda: Post)
    esg_profile = graphene.Field(lambda: EsgProfile)


# ============================================================================
# FINTECH TYPES
# ============================================================================

class Wallet(graphene.ObjectType):
    """User wallet - Fintech domain."""
    id = graphene.String(required=True)
    user_id = graphene.String(required=True)
    balance = graphene.Float(required=True)
    currency = graphene.String(default_value="EUR")
    status = graphene.String(description="active, frozen, closed")
    created_at = graphene.DateTime()
    transactions = graphene.List(lambda: Transaction)


class Transaction(graphene.ObjectType):
    """Financial transaction - Fintech domain."""
    id = graphene.String(required=True)
    wallet_id = graphene.String(required=True)
    amount = graphene.Float(required=True)
    currency = graphene.String()
    transaction_type = graphene.String(description="credit, debit, transfer")
    status = graphene.String(description="pending, completed, failed")
    description = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()


class Payment(graphene.ObjectType):
    """Payment info - Fintech domain."""
    id = graphene.String(required=True)
    transaction_id = graphene.String()
    user_id = graphene.String()
    amount = graphene.Float()
    method = graphene.String(description="card, wallet, bank_transfer")
    status = graphene.String(description="pending, completed, failed, refunded")
    created_at = graphene.DateTime()


# ============================================================================
# MOBILITY TYPES
# ============================================================================

class Vehicle(graphene.ObjectType):
    """Electric vehicle - Mobility domain."""
    id = graphene.String(required=True)
    plate_number = graphene.String()
    model = graphene.String()
    battery_level = graphene.Float(description="0-100%")
    location = graphene.String()
    status = graphene.String(description="available, in_use, charging, maintenance")
    current_ride = graphene.Field(lambda: Ride)


class Ride(graphene.ObjectType):
    """Ride - Mobility domain."""
    id = graphene.String(required=True)
    user_id = graphene.String(required=True)
    vehicle_id = graphene.String()
    start_location = graphene.String()
    end_location = graphene.String()
    distance = graphene.Float(description="kilometers")
    duration = graphene.Int(description="seconds")
    cost = graphene.Float()
    status = graphene.String(description="active, completed, cancelled")
    created_at = graphene.DateTime()
    completed_at = graphene.DateTime()


class Fleet(graphene.ObjectType):
    """Fleet management - Mobility domain."""
    id = graphene.String(required=True)
    name = graphene.String()
    total_vehicles = graphene.Int()
    available_vehicles = graphene.Int()
    optimization_score = graphene.Float(description="0-100")
    vehicles = graphene.List(Vehicle)


# ============================================================================
# ESG TYPES
# ============================================================================

class EsgScore(graphene.ObjectType):
    """ESG score - ESG domain."""
    environmental = graphene.Float(description="0-100")
    social = graphene.Float(description="0-100")
    governance = graphene.Float(description="0-100")
    overall = graphene.Float(description="0-100")
    trend = graphene.String(description="up, stable, down")


class EsgProfile(graphene.ObjectType):
    """User ESG profile - ESG domain."""
    user_id = graphene.String(required=True)
    esg_score = graphene.Field(EsgScore)
    carbon_footprint = graphene.Float(description="kg CO2")
    green_score = graphene.Float(description="0-100")
    pedometer_data = graphene.Field(lambda: PedometerData)
    sustainability_metrics = graphene.List(lambda: SustainabilityMetric)
    last_updated = graphene.DateTime()


class PedometerData(graphene.ObjectType):
    """Pedometer data - ESG domain."""
    user_id = graphene.String()
    date = graphene.String()
    steps = graphene.Int()
    distance = graphene.Float(description="kilometers")
    calories = graphene.Float()
    active_minutes = graphene.Int()


class SustainabilityMetric(graphene.ObjectType):
    """Sustainability metric - ESG domain."""
    metric_name = graphene.String()
    value = graphene.Float()
    unit = graphene.String()
    trend = graphene.String()


# ============================================================================
# SOCIAL TYPES
# ============================================================================

class Post(graphene.ObjectType):
    """Social post - Social domain."""
    id = graphene.String(required=True)
    author_id = graphene.String(required=True)
    content = graphene.String()
    content_type = graphene.String(description="text, image, video")
    engagement_score = graphene.Float(description="0-100")
    created_at = graphene.DateTime()
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    shares_count = graphene.Int()
    comments = graphene.List(lambda: Comment)


class Comment(graphene.ObjectType):
    """Comment on post - Social domain."""
    id = graphene.String(required=True)
    post_id = graphene.String()
    author_id = graphene.String()
    content = graphene.String()
    created_at = graphene.DateTime()


class Feed(graphene.ObjectType):
    """User personalized feed - Social domain."""
    user_id = graphene.String(required=True)
    items = graphene.List(Post)
    total_items = graphene.Int()
    generated_at = graphene.DateTime()


class Recommendation(graphene.ObjectType):
    """Recommendation for user - Social domain."""
    id = graphene.String(required=True)
    user_id = graphene.String()
    target_id = graphene.String(description="user/post/community id")
    recommendation_type = graphene.String(description="content, user, community")
    confidence_score = graphene.Float(description="0-100")
    reason = graphene.String()


# ============================================================================
# PAGINATION & FILTERING
# ============================================================================

class PaginationInput(graphene.InputObjectType):
    """Pagination parameters."""
    limit = graphene.Int(default_value=20)
    offset = graphene.Int(default_value=0)


class TransactionFilter(graphene.InputObjectType):
    """Filter transactions."""
    status = graphene.String()
    transaction_type = graphene.String()
    amount_min = graphene.Float()
    amount_max = graphene.Float()
    date_from = graphene.DateTime()
    date_to = graphene.DateTime()


class PostFilter(graphene.InputObjectType):
    """Filter posts."""
    author_id = graphene.String()
    content_type = graphene.String()
    engagement_min = graphene.Float()
    date_from = graphene.DateTime()
    date_to = graphene.DateTime()


# ============================================================================
# RESPONSE TYPES
# ============================================================================

class ApiResponse(graphene.ObjectType):
    """Generic API response."""
    success = graphene.Boolean(required=True)
    message = graphene.String()
    data = graphene.JSONString()
    errors = graphene.List(graphene.String)


class TransactionConnection(graphene.ObjectType):
    """Paginated transactions."""
    edges = graphene.List(lambda: TransactionEdge)
    page_info = graphene.Field(lambda: PageInfo)
    total_count = graphene.Int()


class TransactionEdge(graphene.ObjectType):
    """Transaction edge for pagination."""
    cursor = graphene.String()
    node = graphene.Field(Transaction)


class PageInfo(graphene.ObjectType):
    """Pagination metadata."""
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    start_cursor = graphene.String()
    end_cursor = graphene.String()
