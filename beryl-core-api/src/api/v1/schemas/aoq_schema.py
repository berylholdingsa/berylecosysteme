"""Pydantic schemas for AOQ APIs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AoqFeatures(BaseModel):
    fintech_score: float = Field(..., ge=0, le=100)
    mobility_score: float = Field(..., ge=0, le=100)
    esg_score: float = Field(..., ge=0, le=100)
    social_score: float = Field(..., ge=0, le=100)


class SignalRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    source: str = Field(default="mobile", min_length=1, max_length=64)
    features: AoqFeatures
    metadata: dict[str, Any] = Field(default_factory=dict)


class SignalResponse(BaseModel):
    signal_id: UUID
    user_id: str
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    signal_id: UUID | None = None
    features: AoqFeatures | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_signal_or_features(self) -> "DecisionRequest":
        if self.signal_id is None and self.features is None:
            raise ValueError("either signal_id or features must be provided")
        return self


class DecisionResponse(BaseModel):
    decision_id: UUID
    signal_id: UUID
    rule_id: UUID
    user_id: str
    score: float
    threshold: float
    decision: str
    rationale: str
    created_at: datetime


class RuleSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    threshold: float = Field(..., ge=0, le=100)
    weight_fintech: float = Field(default=0.35, ge=0, le=1)
    weight_mobility: float = Field(default=0.25, ge=0, le=1)
    weight_esg: float = Field(default=0.25, ge=0, le=1)
    weight_social: float = Field(default=0.15, ge=0, le=1)
    active: bool = True

    @field_validator("weight_social")
    @classmethod
    def validate_weight_sum(cls, weight_social: float, info):
        fintech = info.data.get("weight_fintech", 0.35)
        mobility = info.data.get("weight_mobility", 0.25)
        esg = info.data.get("weight_esg", 0.25)
        total = fintech + mobility + esg + weight_social
        if abs(total - 1.0) > 1e-6:
            raise ValueError("weights must sum to 1.0")
        return weight_social


class RuleResponse(BaseModel):
    id: UUID
    name: str
    threshold: float
    weight_fintech: float
    weight_mobility: float
    weight_esg: float
    weight_social: float
    active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditTrailResponse(BaseModel):
    id: UUID
    event_type: str
    entity_id: str
    payload: dict[str, Any]
    signature: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
