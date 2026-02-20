"""Revenue engine with ledger, audit, signing, and idempotency controls."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from sqlalchemy import func, select

from src.config.settings import settings
from src.core.audit import audit_service
from src.core.security import idempotency_service
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.revenue import RevenueRecordModel
from src.db.sqlalchemy import Base, get_engine, get_session_local
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class RevenueEngine:
    """Records monetization events with full compliance guarantees."""

    def __init__(self, *, session_factory: Callable = lambda: get_session_local()()) -> None:
        self._session_factory = session_factory
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[
                    RevenueRecordModel.__table__,
                    LedgerUserModel.__table__,
                    LedgerAccountModel.__table__,
                    LedgerEntryModel.__table__,
                    IdempotencyKeyModel.__table__,
                ],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=bfos_revenue_bootstrap_skipped reason={str(exc)}")

    def record_revenue(
        self,
        source: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
        *,
        actor_id: str = "bfos-revenue-engine",
        correlation_id: str | None = None,
        session=None,
    ) -> dict:
        normalized_currency = currency.upper().strip()
        normalized_source = source.strip().lower()
        normalized_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if normalized_amount <= 0:
            raise ValueError("revenue amount must be positive")

        correlation = (correlation_id or str(uuid.uuid4())).strip()
        idempotency_key = self._build_idempotency_key(normalized_source, transaction_id)

        if session is None:
            with self._session_factory() as own_session:
                with own_session.begin():
                    result = self._record_revenue_txn(
                        session=own_session,
                        source=normalized_source,
                        amount=normalized_amount,
                        currency=normalized_currency,
                        transaction_id=transaction_id,
                        actor_id=actor_id,
                        correlation_id=correlation,
                        idempotency_key=idempotency_key,
                    )
                return result

        return self._record_revenue_txn(
            session=session,
            source=normalized_source,
            amount=normalized_amount,
            currency=normalized_currency,
            transaction_id=transaction_id,
            actor_id=actor_id,
            correlation_id=correlation,
            idempotency_key=idempotency_key,
        )

    def get_revenue_summary(self, period: str) -> dict:
        since = self._resolve_since(period)
        with self._session_factory() as session:
            stmt = (
                select(
                    RevenueRecordModel.source,
                    RevenueRecordModel.currency,
                    func.sum(RevenueRecordModel.amount).label("total_amount"),
                    func.count(RevenueRecordModel.id).label("count"),
                )
                .group_by(RevenueRecordModel.source, RevenueRecordModel.currency)
                .order_by(RevenueRecordModel.source.asc())
            )
            if since is not None:
                stmt = stmt.where(RevenueRecordModel.created_at >= since)

            rows = list(session.execute(stmt).all())

        total = Decimal("0.00")
        by_source: dict[str, dict] = {}
        for row in rows:
            source = str(row.source)
            currency = str(row.currency)
            subtotal = Decimal(str(row.total_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total += subtotal
            by_source[f"{source}:{currency}"] = {
                "source": source,
                "currency": currency,
                "amount": str(subtotal),
                "count": int(row.count),
            }

        return {
            "period": period,
            "total_amount": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "items": list(by_source.values()),
        }

    def _record_revenue_txn(
        self,
        *,
        session,
        source: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> dict:
        if not idempotency_service.claim_or_reject(session=session, key=idempotency_key, user_id=actor_id[:128]):
            existing = session.execute(
                select(RevenueRecordModel).where(RevenueRecordModel.transaction_id == transaction_id)
            ).scalar_one_or_none()
            if existing is None:
                return {
                    "transaction_id": transaction_id,
                    "source": source,
                    "amount": str(amount),
                    "currency": currency,
                    "idempotent": True,
                }
            return self._serialize(existing, idempotent=True)

        debit_entry_id, credit_entry_id = self._write_double_entry(
            session=session,
            amount=amount,
            currency=currency,
            reference=transaction_id,
            source=source,
        )

        payload = {
            "source": source,
            "amount": str(amount),
            "currency": currency,
            "transaction_id": transaction_id,
            "debit_entry_id": debit_entry_id,
            "credit_entry_id": credit_entry_id,
            "correlation_id": correlation_id,
        }
        payload_hash = self._hash_payload(payload)
        signature = event_signature_verifier.sign(payload)

        record = RevenueRecordModel(
            source=source,
            amount=amount,
            currency=currency,
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            signature=signature,
            correlation_id=correlation_id,
            payload=payload,
            debit_entry_id=debit_entry_id,
            credit_entry_id=credit_entry_id,
        )
        session.add(record)
        session.flush()

        audit_service.record_financial_event(
            session=session,
            actor_id=actor_id,
            action="BFOS_REVENUE_RECORDED",
            amount=amount,
            currency=currency,
            correlation_id=correlation_id,
            payload=payload,
        )

        metrics.record_revenue_total(source=source, currency=currency, amount=float(amount))
        logger.info(
            "event=bfos_revenue_recorded",
            source=source,
            amount=str(amount),
            currency=currency,
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
        )

        return self._serialize(record, idempotent=False)

    def _write_double_entry(self, *, session, amount: Decimal, currency: str, reference: str, source: str) -> tuple[str, str]:
        debit_account = self._ensure_ledger_account(session=session, user_ref=f"{source}:clearing", currency=currency)
        credit_account = self._ensure_ledger_account(session=session, user_ref="bfos:revenue", currency=currency)

        debit = LedgerEntryModel(account_id=debit_account, amount=amount, direction="DEBIT", reference=reference)
        credit = LedgerEntryModel(account_id=credit_account, amount=amount, direction="CREDIT", reference=reference)
        session.add(debit)
        session.add(credit)
        session.flush()
        return str(debit.id), str(credit.id)

    def _ensure_ledger_account(self, *, session, user_ref: str, currency: str) -> uuid.UUID:
        user_uuid = self._stable_uuid(f"ledger-user:{user_ref}")
        account_uuid = self._stable_uuid(f"ledger-account:{user_ref}:{currency}")

        user_row = session.get(LedgerUserModel, user_uuid)
        if user_row is None:
            session.add(LedgerUserModel(id=user_uuid, firebase_uid=user_ref[:128]))

        account_row = session.get(LedgerAccountModel, account_uuid)
        if account_row is None:
            session.add(LedgerAccountModel(id=account_uuid, user_id=user_uuid, currency=currency))

        session.flush()
        return account_uuid

    @staticmethod
    def _stable_uuid(seed: str) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_URL, seed)

    @staticmethod
    def _build_idempotency_key(source: str, transaction_id: str) -> str:
        raw = f"bfos-revenue:{source}:{transaction_id}"
        if len(raw) <= 128:
            return raw
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"bfos-revenue:{digest[:115]}"

    @staticmethod
    def _hash_payload(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _resolve_since(period: str) -> datetime | None:
        normalized = period.strip().lower()
        now = datetime.now(timezone.utc)
        if normalized in {"all", "lifetime"}:
            return None
        if normalized in {"24h", "1d", "day"}:
            return now - timedelta(days=1)
        if normalized in {"7d", "week"}:
            return now - timedelta(days=7)
        if normalized in {"30d", "month"}:
            return now - timedelta(days=30)
        if normalized in {"90d", "quarter"}:
            return now - timedelta(days=90)
        raise ValueError("unsupported period")

    @staticmethod
    def _serialize(record: RevenueRecordModel, *, idempotent: bool) -> dict:
        return {
            "id": str(record.id),
            "source": record.source,
            "amount": str(record.amount),
            "currency": record.currency,
            "transaction_id": record.transaction_id,
            "signature": record.signature,
            "payload_hash": record.payload_hash,
            "debit_entry_id": record.debit_entry_id,
            "credit_entry_id": record.credit_entry_id,
            "idempotent": idempotent,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }


revenue_engine = RevenueEngine()


def record_revenue(source: str, amount: Decimal, currency: str, transaction_id: str, **kwargs) -> dict:
    return revenue_engine.record_revenue(source, amount, currency, transaction_id, **kwargs)


def get_revenue_summary(period: str) -> dict:
    return revenue_engine.get_revenue_summary(period)
