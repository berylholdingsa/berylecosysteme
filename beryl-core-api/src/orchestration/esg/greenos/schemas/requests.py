"""Strict request DTOs for GreenOS v2 endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, field_validator


class StrictSchema(BaseModel):
    """Base schema with strict mode and forbidden extra fields."""

    model_config = ConfigDict(strict=True, extra="forbid")


class RealtimeCalculateRequest(StrictSchema):
    """Input contract for real-time GreenOS CO2 calculation."""

    trip_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    vehicle_id: str = Field(..., min_length=1, max_length=128)
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    distance_km: PositiveFloat
    geo_hash: str = Field(..., min_length=4, max_length=32)
    model_version: str = Field(default="greenos-co2-v1", min_length=1, max_length=64)
    event_timestamp: datetime | None = None

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        upper = value.upper()
        if len(upper) != 2 or not upper.isalpha():
            raise ValueError("country_code must be a 2-letter ISO code")
        return upper


class AuditPreviewQuery(StrictSchema):
    """Query contract for audit preview generation."""

    window: Literal["3M", "6M", "12M"] = "3M"
    country_code: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        upper = value.upper()
        if len(upper) != 2 or not upper.isalpha():
            raise ValueError("country_code must be a 2-letter ISO code")
        return upper


class MrvExportQuery(StrictSchema):
    """Query contract for MRV export generation."""

    period: Literal["3M", "6M", "12M"] = "3M"
