"""FX engine with signed rates, ledger traceability, and compliance hooks."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from sqlalchemy import select

from src.bfos.aoq_hook import optimize_fx_timing, risk_adjustment
from src.bfos.revenue_engine import RevenueEngine, revenue_engine
from src.config.settings import settings
from src.core.audit import audit_service
from src.core.security import idempotency_service
from src.db.models.fx_rates import FxRateModel, FxTransactionModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class FxEngine:
    """Performs USD->CFA conversion with signed rate integrity and audit."""

    def __init__(
        self,
        *,
        session_factory: Callable = lambda: get_session_local()(),
        linked_revenue_engine: RevenueEngine | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._revenue_engine = linked_revenue_engine or revenue_engine
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[
                    FxRateModel.__table__,
                    FxTransactionModel.__table__,
                    IdempotencyKeyModel.__table__,
                    LedgerUserModel.__table__,
                    LedgerAccountModel.__table__,
                    LedgerEntryModel.__table__,
                ],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=bfos_fx_bootstrap_skipped reason={str(exc)}")

    def convert_usd_to_cfa(self, amount_usd: Decimal, *, session=None) -> Decimal:
        amount = Decimal(str(amount_usd))
        if amount <= 0:
            raise ValueError("amount_usd must be positive")

        rate = self.get_current_rate(session=session)
        timing = optimize_fx_timing({"pair": "USD/XOF"})
        multiplier = Decimal(str(timing.get("rate_multiplier", Decimal("1.00"))))
        effective_rate = (rate * multiplier).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        return (amount * effective_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_current_rate(self, *, session=None) -> Decimal:
        if session is None:
            with self._session_factory() as own_session:
                with own_session.begin():
                    return self._get_or_seed_rate(own_session).rate
        return self._get_or_seed_rate(session).rate

    def validate_rate_integrity(self, *, session=None) -> bool:
        if session is None:
            with self._session_factory() as own_session:
                with own_session.begin():
                    return self._validate_rate_integrity_txn(own_session)
        return self._validate_rate_integrity_txn(session)

    def record_fx_transaction(
        self,
        amount_usd: Decimal,
        *,
        transaction_id: str,
        fee_payer: str = "sender",
        actor_id: str = "bfos-fx-engine",
        correlation_id: str | None = None,
        session=None,
    ) -> dict:
        payer = fee_payer.strip().lower()
        if payer not in {"sender", "receiver"}:
            raise ValueError("fee_payer must be sender or receiver")

        normalized_amount = Decimal(str(amount_usd)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if normalized_amount <= 0:
            raise ValueError("amount_usd must be positive")

        idempotency_key = self._build_idempotency_key(transaction_id)
        correlation = correlation_id or str(uuid.uuid4())

        if session is None:
            with self._session_factory() as own_session:
                with own_session.begin():
                    return self._record_fx_txn(
                        session=own_session,
                        amount_usd=normalized_amount,
                        transaction_id=transaction_id,
                        fee_payer=payer,
                        actor_id=actor_id,
                        correlation_id=correlation,
                        idempotency_key=idempotency_key,
                    )

        return self._record_fx_txn(
            session=session,
            amount_usd=normalized_amount,
            transaction_id=transaction_id,
            fee_payer=payer,
            actor_id=actor_id,
            correlation_id=correlation,
            idempotency_key=idempotency_key,
        )

    def _record_fx_txn(
        self,
        *,
        session,
        amount_usd: Decimal,
        transaction_id: str,
        fee_payer: str,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> dict:
        if not idempotency_service.claim_or_reject(session=session, key=idempotency_key, user_id=actor_id[:128]):
            existing = session.execute(
                select(FxTransactionModel).where(FxTransactionModel.transaction_id == transaction_id)
            ).scalar_one_or_none()
            if existing is None:
                return {
                    "transaction_id": transaction_id,
                    "idempotent": True,
                }
            return self._serialize(existing, idempotent=True)

        rate_row = self._get_or_seed_rate(session)
        if not self._validate_rate_row(rate_row):
            raise ValueError("fx rate integrity validation failed")

        gross_cfa = (amount_usd * Decimal(str(rate_row.rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee_rate = Decimal(str(settings.bfos_fx_fee_rate))
        fee_amount_cfa = (gross_cfa * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        risk_profile = risk_adjustment({"pair": "USD/XOF", "amount_usd": str(amount_usd)})
        margin_multiplier = Decimal(str(risk_profile.get("margin_multiplier", Decimal("1.00"))))
        margin_rate = (Decimal(str(settings.bfos_fx_margin_rate)) * margin_multiplier).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        margin_amount_cfa = (gross_cfa * margin_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        settlement_amount = gross_cfa if fee_payer == "sender" else (gross_cfa - fee_amount_cfa)
        debit_entry_id, credit_entry_id = self._write_double_entry(
            session=session,
            amount=settlement_amount,
            currency="XOF",
            reference=transaction_id,
            source="fx_settlement",
        )

        fee_revenue = self._revenue_engine.record_revenue(
            source=f"fx_fee_{fee_payer}",
            amount=fee_amount_cfa,
            currency="XOF",
            transaction_id=f"{transaction_id}:fee",
            actor_id=actor_id,
            correlation_id=correlation_id,
            session=session,
        )
        margin_revenue = self._revenue_engine.record_revenue(
            source="fx_margin",
            amount=margin_amount_cfa,
            currency="XOF",
            transaction_id=f"{transaction_id}:margin",
            actor_id=actor_id,
            correlation_id=correlation_id,
            session=session,
        )

        payload = {
            "transaction_id": transaction_id,
            "amount_usd": str(amount_usd),
            "gross_cfa": str(gross_cfa),
            "settlement_amount": str(settlement_amount),
            "applied_rate": str(rate_row.rate),
            "rate_hash": rate_row.rate_hash,
            "fee_payer": fee_payer,
            "fee_amount_cfa": str(fee_amount_cfa),
            "margin_amount_cfa": str(margin_amount_cfa),
            "debit_entry_id": debit_entry_id,
            "credit_entry_id": credit_entry_id,
            "fee_revenue_id": fee_revenue.get("id"),
            "margin_revenue_id": margin_revenue.get("id"),
            "correlation_id": correlation_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        payload_hash = self._hash_payload(payload)
        signature = event_signature_verifier.sign(payload)

        row = FxTransactionModel(
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
            amount_usd=amount_usd,
            converted_amount_cfa=settlement_amount,
            applied_rate=Decimal(str(rate_row.rate)),
            fee_payer=fee_payer,
            fee_amount_cfa=fee_amount_cfa,
            margin_amount_cfa=margin_amount_cfa,
            payload_hash=payload_hash,
            signature=signature,
            correlation_id=correlation_id,
            payload=payload,
        )
        session.add(row)
        session.flush()

        audit_service.record_financial_event(
            session=session,
            actor_id=actor_id,
            action="BFOS_FX_TRANSACTION_RECORDED",
            amount=settlement_amount,
            currency="XOF",
            correlation_id=correlation_id,
            payload=payload,
        )

        metrics.record_fx_volume(pair="USD/XOF", amount=float(settlement_amount))
        metrics.record_fx_margin(pair="USD/XOF", amount=float(margin_amount_cfa))
        logger.info(
            "event=bfos_fx_transaction_recorded",
            transaction_id=transaction_id,
            fee_payer=fee_payer,
            amount_usd=str(amount_usd),
            settlement_amount=str(settlement_amount),
            applied_rate=str(rate_row.rate),
        )

        return self._serialize(row, idempotent=False)

    def _get_or_seed_rate(self, session) -> FxRateModel:
        row = session.execute(
            select(FxRateModel)
            .where(FxRateModel.base_currency == "USD", FxRateModel.quote_currency == "XOF", FxRateModel.is_active.is_(True))
            .order_by(FxRateModel.created_at.desc())
        ).scalars().first()
        if row is not None:
            return row

        seeded_rate = Decimal(str(settings.bfos_fx_default_usd_xof_rate)).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        payload = {
            "base_currency": "USD",
            "quote_currency": "XOF",
            "rate": str(seeded_rate),
            "source": "bfos-default",
            "seeded_at": datetime.now(timezone.utc).isoformat(),
        }
        row = FxRateModel(
            base_currency="USD",
            quote_currency="XOF",
            rate=seeded_rate,
            rate_hash=self._hash_payload(payload),
            signature=event_signature_verifier.sign(payload),
            source="bfos-default",
            is_active=True,
            payload=payload,
        )
        session.add(row)
        session.flush()
        logger.info("event=bfos_fx_rate_seeded", rate=str(seeded_rate))
        return row

    def _validate_rate_integrity_txn(self, session) -> bool:
        row = self._get_or_seed_rate(session)
        return self._validate_rate_row(row)

    @staticmethod
    def _validate_rate_row(row: FxRateModel) -> bool:
        expected_hash = hashlib.sha256(
            json.dumps(row.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        if expected_hash != row.rate_hash:
            return False

        signed_payload = dict(row.payload)
        signed_payload["signature"] = row.signature
        return event_signature_verifier.verify(signed_payload)

    def _write_double_entry(self, *, session, amount: Decimal, currency: str, reference: str, source: str) -> tuple[str, str]:
        debit_account = self._ensure_ledger_account(session=session, user_ref=f"{source}:debit", currency=currency)
        credit_account = self._ensure_ledger_account(session=session, user_ref=f"{source}:credit", currency=currency)

        debit = LedgerEntryModel(account_id=debit_account, amount=amount, direction="DEBIT", reference=reference)
        credit = LedgerEntryModel(account_id=credit_account, amount=amount, direction="CREDIT", reference=reference)
        session.add(debit)
        session.add(credit)
        session.flush()
        return str(debit.id), str(credit.id)

    def _ensure_ledger_account(self, *, session, user_ref: str, currency: str) -> uuid.UUID:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"fx-ledger-user:{user_ref}")
        account_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"fx-ledger-account:{user_ref}:{currency}")

        if session.get(LedgerUserModel, user_uuid) is None:
            session.add(LedgerUserModel(id=user_uuid, firebase_uid=user_ref[:128]))
        if session.get(LedgerAccountModel, account_uuid) is None:
            session.add(LedgerAccountModel(id=account_uuid, user_id=user_uuid, currency=currency))

        session.flush()
        return account_uuid

    @staticmethod
    def _build_idempotency_key(transaction_id: str) -> str:
        raw = f"bfos-fx:{transaction_id}"
        if len(raw) <= 128:
            return raw
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"bfos-fx:{digest[:120]}"

    @staticmethod
    def _hash_payload(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _serialize(row: FxTransactionModel, *, idempotent: bool) -> dict:
        return {
            "id": str(row.id),
            "transaction_id": row.transaction_id,
            "amount_usd": str(row.amount_usd),
            "converted_amount_cfa": str(row.converted_amount_cfa),
            "applied_rate": str(row.applied_rate),
            "fee_payer": row.fee_payer,
            "fee_amount_cfa": str(row.fee_amount_cfa),
            "margin_amount_cfa": str(row.margin_amount_cfa),
            "signature": row.signature,
            "payload_hash": row.payload_hash,
            "idempotent": idempotent,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


fx_engine = FxEngine()


def convert_usd_to_cfa(amount_usd: Decimal, **kwargs) -> Decimal:
    return fx_engine.convert_usd_to_cfa(amount_usd, **kwargs)


def get_current_rate(**kwargs) -> Decimal:
    return fx_engine.get_current_rate(**kwargs)


def validate_rate_integrity(**kwargs) -> bool:
    return fx_engine.validate_rate_integrity(**kwargs)


def record_fx_transaction(amount_usd: Decimal, **kwargs) -> dict:
    return fx_engine.record_fx_transaction(amount_usd, **kwargs)
