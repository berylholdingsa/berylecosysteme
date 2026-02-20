"""Schemas for fintech, compliance, and audit operations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str


class TransactionRequest(BaseModel):
    actor_id: str = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="XOF", min_length=3, max_length=8)
    target_account: str = Field(min_length=1, max_length=128)


class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    risk_score: float
    aml_flagged: bool
    correlation_id: str


class PaymentRecord(BaseModel):
    transaction_id: str
    actor_id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime


class PaymentsResponse(BaseModel):
    items: list[PaymentRecord]


class OutboxPublishResponse(BaseModel):
    published: int
    failed: int
    dlq: int
    scanned: int


class KafkaConsumeResponse(BaseModel):
    processed: int
    failed: int
    skipped: int
    scanned: int


class AuditEventView(BaseModel):
    event_id: str
    actor_id: str
    action: str
    amount: Decimal | None
    currency: str | None
    correlation_id: str
    previous_hash: str
    current_hash: str
    signature: str
    created_at: datetime


class AuditVerificationResponse(BaseModel):
    ok: bool
    issues: list[str]
