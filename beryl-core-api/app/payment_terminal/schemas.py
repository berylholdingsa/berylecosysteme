"""Schemas for the Smart Payment Terminal module."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PaymentMethod(str, Enum):
    WALLET = "WALLET"
    CARD = "CARD"
    QR = "QR"


class PaymentDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"
    CONFIRMED = "CONFIRMED"


class PaymentInitiateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="XOF", min_length=3, max_length=8)
    merchant_id: str = Field(min_length=1, max_length=128)
    payment_method: PaymentMethod
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class PaymentInitiateResponse(BaseModel):
    status: PaymentStatus
    decision: PaymentDecision
    confidence_score: float = Field(ge=0, le=1)
    terminal_session_id: str


class PaymentConfirmRequest(BaseModel):
    terminal_session_id: str = Field(min_length=36, max_length=64)
    biometric_verified: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaymentConfirmResponse(BaseModel):
    status: PaymentStatus
    decision: PaymentDecision
    confidence_score: float = Field(ge=0, le=1)
    terminal_session_id: str


class PaymentSessionResponse(BaseModel):
    status: PaymentStatus
    risk_score: float = Field(ge=0, le=1)
    ai_flags: list[str] = Field(default_factory=list)
    decision: PaymentDecision
    confidence_score: float = Field(ge=0, le=1)
    transaction_id: str


class UnifiedErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None
    correlation_id: str

