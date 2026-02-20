"""Fintech routes with compliance, immutable audit, and outbox relay."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.api.v1.schemas.fintech_schema import (
    AuditEventView,
    AuditVerificationResponse,
    KafkaConsumeResponse,
    OutboxPublishResponse,
    PaymentRecord,
    PaymentsResponse,
    TransactionRequest,
    TransactionResponse,
)
from src.bfos.accounting.statement_engine import statement_engine
from src.bfos.fee_engine import calculate_internal_transfer_fee
from src.bfos.fx_engine import get_current_rate, record_fx_transaction, validate_rate_integrity
from src.bfos.revenue_engine import get_revenue_summary, record_revenue
from src.bfos.tontine.tontine_engine import tontine_engine
from src.compliance import suspicious_activity_log_service, transaction_risk_scorer
from src.core.audit import audit_service
from src.core.security import idempotency_service
from src.db.models.fx_rates import FxRateModel, FxTransactionModel
from src.db.models.fintech import FintechTransactionModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.compliance import SuspiciousActivityLogModel
from src.db.models.revenue import RevenueRecordModel
from src.db.models.statements import CertifiedStatementModel, StatementSignatureModel
from src.db.models.tontine import (
    TontineCycleModel,
    TontineGroupModel,
    TontineMemberModel,
    TontineVoteModel,
    TontineWithdrawRequestModel,
)
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.events.bus.event_bus import get_event_bus
from src.events.outbox_relay import outbox_relay_service
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics

router = APIRouter()

try:
    Base.metadata.create_all(
        bind=get_engine(),
        tables=[
            FintechTransactionModel.__table__,
            IdempotencyKeyModel.__table__,
            SuspiciousActivityLogModel.__table__,
            RevenueRecordModel.__table__,
            LedgerUserModel.__table__,
            LedgerAccountModel.__table__,
            LedgerEntryModel.__table__,
            FxRateModel.__table__,
            FxTransactionModel.__table__,
            CertifiedStatementModel.__table__,
            StatementSignatureModel.__table__,
            TontineGroupModel.__table__,
            TontineMemberModel.__table__,
            TontineCycleModel.__table__,
            TontineWithdrawRequestModel.__table__,
            TontineVoteModel.__table__,
        ],
        checkfirst=True,
    )
except Exception as exc:  # pragma: no cover
    logger.warning(f"event=fintech_models_bootstrap_skipped reason={str(exc)}")


class FxConversionRequest(BaseModel):
    amount_usd: Decimal = Field(gt=0)
    fee_payer: str = Field(default="sender", pattern="^(sender|receiver)$")
    transaction_id: str | None = Field(default=None, max_length=128)
    actor_id: str = Field(default="fintech-api", min_length=1, max_length=128)


class FxConversionResponse(BaseModel):
    transaction_id: str
    amount_usd: str
    converted_amount_cfa: str
    applied_rate: str
    fee_payer: str
    fee_amount_cfa: str
    margin_amount_cfa: str
    signature: str
    payload_hash: str
    idempotent: bool
    current_rate: str


class StatementGenerateRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    period: str = Field(pattern="^(3m|6m|12m)$")
    merchant_name: str | None = Field(default=None, max_length=256)


class StatementGenerateResponse(BaseModel):
    statement_id: str
    user_id: str
    period: str
    statement_fee: str
    currency: str
    pdf_hash: str
    signature: str
    signature_algorithm: str
    signature_key_id: str
    verification_url: str
    immutable: bool
    idempotent: bool
    created_at: str | None


class StatementVerifyResponse(BaseModel):
    exists: bool
    valid: bool
    statement_id: str | None = None
    hash_ok: bool | None = None
    signature_ok: bool | None = None
    pdf_hash: str | None = None
    computed_hash: str | None = None
    verification_url: str | None = None
    reason: str | None = None


class TontineCreateRequest(BaseModel):
    community_group_id: str = Field(min_length=1, max_length=128)
    created_by: str = Field(min_length=1, max_length=128)
    contribution_amount: Decimal = Field(gt=0)
    frequency_type: str = Field(pattern="^(DAILY|WEEKLY|BIWEEKLY|MONTHLY)$")
    security_code: str = Field(pattern="^\\d{5}$")
    max_members: int = Field(default=10, ge=2, le=10)


class TontineJoinRequest(BaseModel):
    tontine_id: str = Field(min_length=36, max_length=64)
    user_id: str = Field(min_length=1, max_length=128)


class TontineContributionRequest(BaseModel):
    tontine_id: str = Field(min_length=36, max_length=64)
    user_id: str = Field(min_length=1, max_length=128)
    amount: Decimal | None = Field(default=None, gt=0)


class TontineWithdrawRequestPayload(BaseModel):
    tontine_id: str = Field(min_length=36, max_length=64)
    requested_by: str = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0)
    security_code: str = Field(pattern="^\\d{5}$")


class TontineVoteRequest(BaseModel):
    tontine_id: str = Field(min_length=36, max_length=64)
    withdraw_request_id: str = Field(min_length=36, max_length=64)
    user_id: str = Field(min_length=1, max_length=128)
    approved: bool
    security_code: str = Field(pattern="^\\d{5}$")


class TontineSnapshotResponse(BaseModel):
    tontine_id: str
    balance: str
    frequency_type: str
    next_distribution_date: str | None
    masked: bool
    status: str
    member_count: int | None = None
    max_members: int | None = None
    contribution_amount: str | None = None
    current_cycle_number: int | None = None
    withdraw_request_id: str | None = None
    withdraw_status: str | None = None
    fee_amount: str | None = None
    idempotent: bool | None = None


class TontineBalanceResponse(BaseModel):
    tontine_id: str
    balance: str
    frequency_type: str
    next_distribution_date: str | None
    masked: bool
    status: str


class TransferPreviewRequest(BaseModel):
    actor_id: str = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="XOF", min_length=3, max_length=8)
    destination_country: str = Field(min_length=2, max_length=3)
    exchange_rate: Decimal | None = Field(default=None, gt=0)


class TransferPreviewResponse(BaseModel):
    gross_amount: str
    fee_amount: str
    net_amount: str
    exchange_rate: str | None = None


class TransferExecuteRequest(BaseModel):
    actor_id: str = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="XOF", min_length=3, max_length=8)
    destination_country: str = Field(min_length=2, max_length=3)
    target_account: str = Field(min_length=1, max_length=128)
    reference: str | None = Field(default=None, max_length=128)
    exchange_rate: Decimal | None = Field(default=None, gt=0)


class TransferExecuteResponse(BaseModel):
    transaction_id: str
    status: str
    risk_score: float
    aml_flagged: bool
    gross_amount: str
    fee_amount: str
    net_amount: str
    exchange_rate: str | None = None
    currency: str
    correlation_id: str
    ledger_debit_entry_id: str
    ledger_credit_entry_id: str
    fee_revenue_id: str | None = None


def _raise_tontine_http_error(exc: ValueError) -> None:
    message = str(exc)
    lowered = message.lower()
    if "duplicate idempotency key" in lowered:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
    if "not found" in lowered:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
    if "security code" in lowered:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


def _quantize_amount(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _format_exchange_rate(rate: Decimal | None) -> str | None:
    if rate is None:
        return None
    return str(Decimal(str(rate)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _compute_transfer_breakdown(
    *,
    session,
    actor_id: str,
    amount: Decimal,
    currency: str,
    correlation_id: str,
    transaction_id: str,
    exchange_rate: Decimal | None,
) -> tuple[Decimal, Decimal, Decimal, str | None]:
    gross_amount = _quantize_amount(amount)
    fee_amount = calculate_internal_transfer_fee(
        gross_amount,
        session=session,
        actor_id=actor_id,
        currency=currency,
        correlation_id=correlation_id,
        transaction_id=transaction_id,
    )
    fee_amount = _quantize_amount(fee_amount)
    net_amount = _quantize_amount(gross_amount - fee_amount)
    if net_amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="transfer net amount must be positive")

    return gross_amount, fee_amount, net_amount, _format_exchange_rate(exchange_rate)


def _stable_uuid(seed: str) -> UUID:
    return uuid5(NAMESPACE_URL, seed)


def _ensure_transfer_ledger_account(*, session, user_ref: str, currency: str) -> UUID:
    user_uuid = _stable_uuid(f"transfer-ledger-user:{user_ref}")
    account_uuid = _stable_uuid(f"transfer-ledger-account:{user_ref}:{currency}")

    if session.get(LedgerUserModel, user_uuid) is None:
        session.add(LedgerUserModel(id=user_uuid, firebase_uid=user_ref[:128]))

    if session.get(LedgerAccountModel, account_uuid) is None:
        session.add(LedgerAccountModel(id=account_uuid, user_id=user_uuid, currency=currency))

    session.flush()
    return account_uuid


def _write_transfer_double_entry(
    *,
    session,
    amount: Decimal,
    currency: str,
    reference: str,
    actor_id: str,
    target_account: str,
    destination_country: str,
) -> tuple[str, str]:
    debit_account = _ensure_transfer_ledger_account(
        session=session,
        user_ref=f"transfer:sender:{actor_id}",
        currency=currency,
    )
    credit_account = _ensure_transfer_ledger_account(
        session=session,
        user_ref=f"transfer:receiver:{destination_country}:{target_account}",
        currency=currency,
    )

    debit = LedgerEntryModel(account_id=debit_account, amount=amount, direction="DEBIT", reference=reference)
    credit = LedgerEntryModel(account_id=credit_account, amount=amount, direction="CREDIT", reference=reference)
    session.add(debit)
    session.add(credit)
    session.flush()
    return str(debit.id), str(credit.id)


@router.post("/transfer/preview", response_model=TransferPreviewResponse)
def preview_transfer(request: TransferPreviewRequest, http_request: Request):
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    preview_id = f"preview-{uuid4()}"

    with get_session_local()() as session:
        with session.begin():
            gross_amount, fee_amount, net_amount, formatted_exchange_rate = _compute_transfer_breakdown(
                session=session,
                actor_id=request.actor_id,
                amount=request.amount,
                currency=request.currency,
                correlation_id=correlation_id,
                transaction_id=preview_id,
                exchange_rate=request.exchange_rate,
            )

            audit_service.record_financial_event(
                session=session,
                actor_id=request.actor_id,
                action="TRANSFER_PREVIEWED",
                amount=gross_amount,
                currency=request.currency,
                correlation_id=correlation_id,
                payload={
                    "preview_id": preview_id,
                    "destination_country": request.destination_country.upper(),
                    "gross_amount": str(gross_amount),
                    "fee_amount": str(fee_amount),
                    "net_amount": str(net_amount),
                    "exchange_rate": formatted_exchange_rate,
                },
            )

    return TransferPreviewResponse(
        gross_amount=str(gross_amount),
        fee_amount=str(fee_amount),
        net_amount=str(net_amount),
        exchange_rate=formatted_exchange_rate,
    )


@router.post("/transfer", response_model=TransferExecuteResponse)
def execute_transfer(
    request: TransferExecuteRequest,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")

    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    transaction_uuid = uuid4()
    transaction_id = str(transaction_uuid)
    destination_country = request.destination_country.upper()

    with get_session_local()() as session:
        with session.begin():
            if not idempotency_service.claim_or_reject(
                session=session,
                key=idempotency_key,
                user_id=request.actor_id,
            ):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate idempotency key")

            risk = transaction_risk_scorer.assess(
                actor_id=request.actor_id,
                amount=float(request.amount),
                currency=request.currency,
            )
            metrics.observe_fintech_risk_score(risk.score)

            gross_amount, fee_amount, net_amount, formatted_exchange_rate = _compute_transfer_breakdown(
                session=session,
                actor_id=request.actor_id,
                amount=request.amount,
                currency=request.currency,
                correlation_id=correlation_id,
                transaction_id=transaction_id,
                exchange_rate=request.exchange_rate,
            )

            tx = FintechTransactionModel(
                id=transaction_uuid,
                actor_id=request.actor_id,
                amount=gross_amount,
                currency=request.currency,
                target_account=request.target_account,
                status="FLAGGED" if risk.flagged else "ACCEPTED",
                risk_score=Decimal(str(round(risk.score, 2))),
                aml_flagged=risk.flagged,
                correlation_id=correlation_id,
            )
            session.add(tx)
            session.flush()

            ledger_debit_entry_id, ledger_credit_entry_id = _write_transfer_double_entry(
                session=session,
                amount=net_amount,
                currency=request.currency,
                reference=transaction_id,
                actor_id=request.actor_id,
                target_account=request.target_account,
                destination_country=destination_country,
            )

            fee_revenue = record_revenue(
                source="internal_transfer_fee",
                amount=fee_amount,
                currency=request.currency,
                transaction_id=f"{transaction_id}:fee",
                actor_id=request.actor_id,
                correlation_id=correlation_id,
                session=session,
            )

            if risk.flagged:
                suspicious_activity_log_service.record(
                    session=session,
                    transaction_id=transaction_id,
                    actor_id=request.actor_id,
                    risk_score=risk.score,
                    reasons=risk.reasons,
                    correlation_id=correlation_id,
                )
                metrics.record_aml_flag(reason=",".join(risk.reasons) if risk.reasons else "threshold")

            audit_service.record_financial_event(
                session=session,
                actor_id=request.actor_id,
                action="TRANSFER_EXECUTED",
                amount=gross_amount,
                currency=request.currency,
                correlation_id=correlation_id,
                payload={
                    "transaction_id": transaction_id,
                    "target_account": request.target_account,
                    "reference": request.reference,
                    "destination_country": destination_country,
                    "gross_amount": str(gross_amount),
                    "fee_amount": str(fee_amount),
                    "net_amount": str(net_amount),
                    "exchange_rate": formatted_exchange_rate,
                    "ledger_debit_entry_id": ledger_debit_entry_id,
                    "ledger_credit_entry_id": ledger_credit_entry_id,
                    "fee_revenue_id": fee_revenue.get("id"),
                    "risk_score": risk.score,
                    "aml_flagged": risk.flagged,
                    "reasons": risk.reasons,
                },
            )

    return TransferExecuteResponse(
        transaction_id=transaction_id,
        status="FLAGGED" if risk.flagged else "ACCEPTED",
        risk_score=risk.score,
        aml_flagged=risk.flagged,
        gross_amount=str(gross_amount),
        fee_amount=str(fee_amount),
        net_amount=str(net_amount),
        exchange_rate=formatted_exchange_rate,
        currency=request.currency,
        correlation_id=correlation_id,
        ledger_debit_entry_id=ledger_debit_entry_id,
        ledger_credit_entry_id=ledger_credit_entry_id,
        fee_revenue_id=fee_revenue.get("id"),
    )


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    request: TransactionRequest,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")

    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    transaction_uuid = uuid4()
    transaction_id = str(transaction_uuid)

    with get_session_local()() as session:
        with session.begin():
            if not idempotency_service.claim_or_reject(
                session=session,
                key=idempotency_key,
                user_id=request.actor_id,
            ):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate idempotency key")

            risk = transaction_risk_scorer.assess(
                actor_id=request.actor_id,
                amount=float(request.amount),
                currency=request.currency,
            )
            metrics.observe_fintech_risk_score(risk.score)

            tx = FintechTransactionModel(
                id=transaction_uuid,
                actor_id=request.actor_id,
                amount=Decimal(request.amount),
                currency=request.currency,
                target_account=request.target_account,
                status="FLAGGED" if risk.flagged else "ACCEPTED",
                risk_score=Decimal(str(round(risk.score, 2))),
                aml_flagged=risk.flagged,
                correlation_id=correlation_id,
            )
            session.add(tx)
            session.flush()

            fee_amount = calculate_internal_transfer_fee(
                request.amount,
                session=session,
                actor_id=request.actor_id,
                currency=request.currency,
                correlation_id=correlation_id,
                transaction_id=transaction_id,
            )
            fee_revenue = record_revenue(
                source="internal_transfer_fee",
                amount=fee_amount,
                currency=request.currency,
                transaction_id=f"{transaction_id}:fee",
                actor_id=request.actor_id,
                correlation_id=correlation_id,
                session=session,
            )

            if risk.flagged:
                suspicious_activity_log_service.record(
                    session=session,
                    transaction_id=transaction_id,
                    actor_id=request.actor_id,
                    risk_score=risk.score,
                    reasons=risk.reasons,
                    correlation_id=correlation_id,
                )
                metrics.record_aml_flag(reason=",".join(risk.reasons) if risk.reasons else "threshold")

            audit_service.record_financial_event(
                session=session,
                actor_id=request.actor_id,
                action="TRANSACTION_CREATE",
                amount=request.amount,
                currency=request.currency,
                correlation_id=correlation_id,
                payload={
                    "transaction_id": transaction_id,
                    "target_account": request.target_account,
                    "risk_score": risk.score,
                    "aml_flagged": risk.flagged,
                    "reasons": risk.reasons,
                    "fee_amount": str(fee_amount),
                    "fee_revenue_id": fee_revenue.get("id"),
                },
            )

            topic = "fintech.suspicious.activity" if risk.flagged else "fintech.transaction.completed"
            event_payload = {
                "event_id": str(uuid4()),
                "event_type": topic,
                "transaction_id": transaction_id,
                "actor_id": request.actor_id,
                "amount": float(request.amount),
                "currency": request.currency,
                "risk_score": float(risk.score),
                "reasons": ",".join(risk.reasons),
                "fee_amount": float(fee_amount),
                "fee_revenue_id": fee_revenue.get("id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "correlation_id": correlation_id,
            }
            signature = event_signature_verifier.sign(event_payload)
            outbox_relay_service.stage_event(
                session=session,
                topic=topic,
                event_key=transaction_id,
                payload=event_payload,
                signature=signature,
            )

    await outbox_relay_service.publish_pending(limit=100)

    return TransactionResponse(
        transaction_id=transaction_id,
        status="FLAGGED" if risk.flagged else "ACCEPTED",
        risk_score=risk.score,
        aml_flagged=risk.flagged,
        correlation_id=correlation_id,
    )


@router.get("/payments", response_model=PaymentsResponse)
def get_payments(limit: int = 50):
    with get_session_local()() as session:
        rows = list(
            session.execute(
                select(FintechTransactionModel)
                .order_by(FintechTransactionModel.created_at.desc())
                .limit(max(1, min(200, limit)))
            ).scalars().all()
        )

    return PaymentsResponse(
        items=[
            PaymentRecord(
                transaction_id=str(row.id),
                actor_id=row.actor_id,
                amount=Decimal(row.amount),
                currency=row.currency,
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


@router.post("/outbox/publish", response_model=OutboxPublishResponse)
async def publish_outbox():
    result = await outbox_relay_service.publish_pending(limit=200)
    return OutboxPublishResponse(**result)


@router.post("/events/consume", response_model=KafkaConsumeResponse)
async def consume_kafka_events():
    bus = await get_event_bus()
    if getattr(bus, "broker_type", "mock") != "kafka":
        return KafkaConsumeResponse(processed=0, failed=0, skipped=0, scanned=0)

    topics = [topic.strip() for topic in bus._required_signed_topics]  # pylint: disable=protected-access

    def _handler(topic: str, payload: dict) -> None:
        _ = topic
        _ = payload

    result = await bus.consume_batch(topics=topics, handler=_handler, max_records=200, timeout_ms=1000)
    return KafkaConsumeResponse(**result)


@router.get("/audit/events", response_model=list[AuditEventView])
def list_audit_events(limit: int = 50, offset: int = 0):
    rows = audit_service.list_events(limit=max(1, min(200, limit)), offset=max(0, offset))
    return [
        AuditEventView(
            event_id=row.event_id,
            actor_id=row.actor_id,
            action=row.action,
            amount=row.amount,
            currency=row.currency,
            correlation_id=row.correlation_id,
            previous_hash=row.previous_hash,
            current_hash=row.current_hash,
            signature=row.signature,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/audit/verify", response_model=AuditVerificationResponse)
def verify_audit_chain():
    ok, issues = audit_service.verify_integrity()
    return AuditVerificationResponse(ok=ok, issues=issues)


@router.get("/revenue/summary")
def revenue_summary(period: str = "30d"):
    return get_revenue_summary(period)


@router.post("/fx/convert", response_model=FxConversionResponse)
def convert_fx(request: FxConversionRequest, http_request: Request):
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    transaction_id = request.transaction_id or f"fx-{uuid4()}"

    if not validate_rate_integrity():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="FX rate integrity check failed")

    result = record_fx_transaction(
        amount_usd=request.amount_usd,
        transaction_id=transaction_id,
        fee_payer=request.fee_payer,
        actor_id=request.actor_id,
        correlation_id=correlation_id,
    )
    current_rate = get_current_rate()
    return FxConversionResponse(
        transaction_id=result["transaction_id"],
        amount_usd=result["amount_usd"],
        converted_amount_cfa=result["converted_amount_cfa"],
        applied_rate=result["applied_rate"],
        fee_payer=result["fee_payer"],
        fee_amount_cfa=result["fee_amount_cfa"],
        margin_amount_cfa=result["margin_amount_cfa"],
        signature=result["signature"],
        payload_hash=result["payload_hash"],
        idempotent=bool(result["idempotent"]),
        current_rate=str(current_rate),
    )


@router.post("/statements/generate", response_model=StatementGenerateResponse)
def generate_certified_statement(
    request: StatementGenerateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")
    try:
        result = statement_engine.generate_statement(
            request.user_id,
            request.period,
            idempotency_key=idempotency_key,
            merchant_name=request.merchant_name,
        )
        return StatementGenerateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/statements/{statement_id}", response_model=StatementGenerateResponse)
def get_statement(statement_id: str):
    result = statement_engine.get_statement(statement_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")
    return StatementGenerateResponse(**result)


@router.get("/statements/{statement_id}/verify", response_model=StatementVerifyResponse)
def verify_statement(statement_id: str):
    result = statement_engine.verify_statement(statement_id)
    if not result.get("exists", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")
    return StatementVerifyResponse(**result)


@router.post("/tontine/create", response_model=TontineSnapshotResponse)
def create_tontine_group(
    request: TontineCreateRequest,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    try:
        result = tontine_engine.create_tontine(
            community_group_id=request.community_group_id,
            created_by=request.created_by,
            contribution_amount=request.contribution_amount,
            frequency_type=request.frequency_type,
            security_code=request.security_code,
            max_members=request.max_members,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return TontineSnapshotResponse(**result)
    except ValueError as exc:
        _raise_tontine_http_error(exc)


@router.post("/tontine/join", response_model=TontineSnapshotResponse)
def join_tontine_group(
    request: TontineJoinRequest,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    try:
        result = tontine_engine.join_tontine(
            tontine_id=request.tontine_id,
            user_id=request.user_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return TontineSnapshotResponse(**result)
    except ValueError as exc:
        _raise_tontine_http_error(exc)


@router.post("/tontine/contribute", response_model=TontineSnapshotResponse)
def contribute_tontine(
    request: TontineContributionRequest,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    try:
        result = tontine_engine.contribute(
            tontine_id=request.tontine_id,
            user_id=request.user_id,
            amount=request.amount,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return TontineSnapshotResponse(**result)
    except ValueError as exc:
        _raise_tontine_http_error(exc)


@router.post("/tontine/request-withdraw", response_model=TontineSnapshotResponse)
def request_tontine_withdraw(
    request: TontineWithdrawRequestPayload,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    try:
        result = tontine_engine.request_withdraw(
            tontine_id=request.tontine_id,
            requested_by=request.requested_by,
            amount=request.amount,
            security_code=request.security_code,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return TontineSnapshotResponse(**result)
    except ValueError as exc:
        _raise_tontine_http_error(exc)


@router.post("/tontine/vote", response_model=TontineSnapshotResponse)
def vote_tontine_withdraw(
    request: TontineVoteRequest,
    http_request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header required")
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid4()))
    try:
        result = tontine_engine.vote_withdraw(
            tontine_id=request.tontine_id,
            withdraw_request_id=request.withdraw_request_id,
            user_id=request.user_id,
            approved=request.approved,
            security_code=request.security_code,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return TontineSnapshotResponse(**result)
    except ValueError as exc:
        _raise_tontine_http_error(exc)


@router.get("/tontine/{tontine_id}", response_model=TontineSnapshotResponse)
def get_tontine_group(tontine_id: str, security_code: str | None = None):
    result = tontine_engine.get_tontine(tontine_id=tontine_id, security_code=security_code)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tontine not found")
    return TontineSnapshotResponse(**result)


@router.get("/tontine/{tontine_id}/wallet-balance", response_model=TontineBalanceResponse)
def get_tontine_wallet_balance(tontine_id: str, security_code: str | None = None):
    result = tontine_engine.get_wallet_balance(tontine_id=tontine_id, security_code=security_code)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tontine not found")
    return TontineBalanceResponse(**result)
