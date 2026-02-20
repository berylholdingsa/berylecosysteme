"""Certified statement generation engine with fee, ledger, audit, and signature."""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable

from sqlalchemy import select

from src.bfos.accounting.merchant_accounting_engine import merchant_accounting_engine, MerchantAccountingEngine
from src.bfos.accounting.pdf_generator import generate_statement_pdf
from src.bfos.accounting.statement_signer import StatementSigner, statement_signer
from src.bfos.fee_engine import fee_engine, FeeEngine
from src.bfos.revenue_engine import revenue_engine, RevenueEngine
from src.config.settings import settings
from src.core.audit import audit_service
from src.core.security import idempotency_service
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.statements import CertifiedStatementModel, StatementSignatureModel
from src.db.sqlalchemy import Base, SessionLocal, get_engine
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class StatementEngine:
    """Creates immutable certified statements signed by Beryl key material."""

    def __init__(
        self,
        *,
        session_factory: Callable = SessionLocal,
        accounting: MerchantAccountingEngine | None = None,
        fees: FeeEngine | None = None,
        revenues: RevenueEngine | None = None,
        signer: StatementSigner | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._accounting = accounting or merchant_accounting_engine
        self._fees = fees or fee_engine
        self._revenues = revenues or revenue_engine
        self._signer = signer or statement_signer

        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[
                    CertifiedStatementModel.__table__,
                    StatementSignatureModel.__table__,
                    IdempotencyKeyModel.__table__,
                ],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=bfos_statement_bootstrap_skipped reason={str(exc)}")

    def generate_statement(
        self,
        user_id: str,
        period: str,
        *,
        idempotency_key: str,
        merchant_name: str | None = None,
    ) -> dict:
        period_label, start_date, end_date = self._resolve_period(period)

        with self._session_factory() as session:
            with session.begin():
                if not idempotency_service.claim_or_reject(session=session, key=idempotency_key, user_id=user_id):
                    existing = session.execute(
                        select(CertifiedStatementModel).where(CertifiedStatementModel.idempotency_key == idempotency_key)
                    ).scalar_one_or_none()
                    if existing is None:
                        raise ValueError("duplicate idempotency key with missing statement")
                    return self._serialize(existing, idempotent=True)

                aggregated = self._accounting.aggregate_transactions(user_id, start_date, end_date)
                summary = aggregated["summary"]
                cashflow = aggregated["cashflow"]
                total_period_amount = Decimal(str(summary["total_sales"]))
                if total_period_amount <= 0:
                    raise ValueError("no eligible sales found for certified statement generation")

                fee_amount = self.calculate_statement_fee(
                    total_period_amount,
                    session=session,
                    actor_id=user_id,
                    correlation_id=f"stmt-{user_id}-{period_label}",
                )
                revenue_record = self.record_statement_revenue(
                    session=session,
                    user_id=user_id,
                    fee_amount=fee_amount,
                    statement_reference=f"{user_id}:{period_label}:{idempotency_key}",
                    correlation_id=f"stmt-{user_id}-{period_label}",
                )

                statement_uuid = uuid.uuid4()
                statement_id = f"stmt-{statement_uuid}"
                merchant = merchant_name or user_id
                verification_url = (
                    f"{settings.bfos_statement_verification_base_url.rstrip('/')}/{statement_id}/verify"
                )

                provisional_pdf = generate_statement_pdf(
                    merchant_name=merchant,
                    user_id=user_id,
                    period_label=period_label,
                    period_start=start_date.isoformat(),
                    period_end=end_date.isoformat(),
                    total_sales=Decimal(str(summary["total_sales"])),
                    total_charges=Decimal(str(summary["total_charges"])),
                    net_result=Decimal(str(summary["net_result"])),
                    cashflow=Decimal(str(cashflow["net_cashflow"])),
                    statement_fee=fee_amount,
                    currency=str(summary["currency"]),
                    document_hash="0" * 64,
                    verification_url=verification_url,
                )
                embedded_hash = hashlib.sha256(provisional_pdf).hexdigest()

                final_pdf = generate_statement_pdf(
                    merchant_name=merchant,
                    user_id=user_id,
                    period_label=period_label,
                    period_start=start_date.isoformat(),
                    period_end=end_date.isoformat(),
                    total_sales=Decimal(str(summary["total_sales"])),
                    total_charges=Decimal(str(summary["total_charges"])),
                    net_result=Decimal(str(summary["net_result"])),
                    cashflow=Decimal(str(cashflow["net_cashflow"])),
                    statement_fee=fee_amount,
                    currency=str(summary["currency"]),
                    document_hash=embedded_hash,
                    verification_url=verification_url,
                )
                pdf_hash = hashlib.sha256(final_pdf).hexdigest()

                signature = self._signer.sign_document(pdf_hash)
                if not self._signer.verify_signature(pdf_hash, signature):
                    raise ValueError("statement signature validation failed")

                statement_row = self.persist_statement_hash(
                    session=session,
                    statement_id=statement_id,
                    user_id=user_id,
                    merchant_name=merchant,
                    period_label=period_label,
                    period_start=start_date,
                    period_end=end_date,
                    total_sales=Decimal(str(summary["total_sales"])),
                    total_charges=Decimal(str(summary["total_charges"])),
                    net_result=Decimal(str(summary["net_result"])),
                    cashflow=Decimal(str(cashflow["net_cashflow"])),
                    statement_fee=fee_amount,
                    currency=str(summary["currency"]),
                    pdf_blob=final_pdf,
                    pdf_hash=pdf_hash,
                    embedded_hash=embedded_hash,
                    signature=signature,
                    idempotency_key=idempotency_key,
                    verification_url=verification_url,
                    revenue_record_id=revenue_record.get("id"),
                )

                signature_meta = self._signer.metadata()
                session.add(
                    StatementSignatureModel(
                        statement_ref=statement_row.id,
                        signed_hash=pdf_hash,
                        signature=signature,
                        algorithm=signature_meta.algorithm,
                        public_key_pem=signature_meta.public_key_pem,
                    )
                )

                audit_service.record_financial_event(
                    session=session,
                    actor_id=user_id,
                    action="BFOS_CERTIFIED_STATEMENT_GENERATED",
                    amount=fee_amount,
                    currency=str(summary["currency"]),
                    correlation_id=f"stmt-{statement_id}",
                    payload={
                        "statement_id": statement_id,
                        "period": period_label,
                        "pdf_hash": pdf_hash,
                        "embedded_hash": embedded_hash,
                        "signature": signature,
                        "verification_url": verification_url,
                        "statement_fee": str(fee_amount),
                    },
                )

                metrics.record_statement_generated(period=period_label)
                metrics.record_statement_fee_collected(currency=str(summary["currency"]), amount=float(fee_amount))

                logger.info(
                    "event=bfos_statement_generated",
                    statement_id=statement_id,
                    user_id=user_id,
                    period=period_label,
                    statement_fee=str(fee_amount),
                )

                return self._serialize(statement_row, idempotent=False)

    def calculate_statement_fee(
        self,
        total_amount: Decimal,
        *,
        session,
        actor_id: str,
        correlation_id: str,
    ) -> Decimal:
        return self._fees.calculate_certified_statement_fee(
            total_amount,
            session=session,
            actor_id=actor_id,
            correlation_id=correlation_id,
            transaction_id=f"statement-fee-{uuid.uuid4()}",
            currency=settings.bfos_statement_currency,
        ).fee_amount

    def record_statement_revenue(
        self,
        *,
        session,
        user_id: str,
        fee_amount: Decimal,
        statement_reference: str,
        correlation_id: str,
    ) -> dict:
        return self._revenues.record_revenue(
            source="certified_statement_fee",
            amount=fee_amount,
            currency=settings.bfos_statement_currency,
            transaction_id=f"statement-fee:{statement_reference}",
            actor_id=user_id,
            correlation_id=correlation_id,
            session=session,
        )

    def persist_statement_hash(self, *, session, **kwargs) -> CertifiedStatementModel:
        signature_meta = self._signer.metadata()
        row = CertifiedStatementModel(
            statement_id=kwargs["statement_id"],
            user_id=kwargs["user_id"],
            merchant_name=kwargs["merchant_name"],
            period_label=kwargs["period_label"],
            period_start=kwargs["period_start"],
            period_end=kwargs["period_end"],
            total_sales=kwargs["total_sales"],
            total_charges=kwargs["total_charges"],
            net_result=kwargs["net_result"],
            cashflow=kwargs["cashflow"],
            statement_fee=kwargs["statement_fee"],
            currency=kwargs["currency"],
            pdf_blob=kwargs["pdf_blob"],
            pdf_hash=kwargs["pdf_hash"],
            embedded_hash=kwargs["embedded_hash"],
            signature=kwargs["signature"],
            signature_algorithm=signature_meta.algorithm,
            signature_key_id=signature_meta.key_id,
            verification_url=kwargs["verification_url"],
            idempotency_key=kwargs["idempotency_key"],
            revenue_record_id=kwargs["revenue_record_id"],
            immutable=True,
        )
        session.add(row)
        session.flush()
        return row

    def get_statement(self, statement_id: str) -> dict | None:
        with self._session_factory() as session:
            row = session.execute(
                select(CertifiedStatementModel).where(CertifiedStatementModel.statement_id == statement_id)
            ).scalar_one_or_none()
            if row is None:
                return None
            return self._serialize(row, idempotent=False)

    def verify_statement(self, statement_id: str) -> dict:
        with self._session_factory() as session:
            row = session.execute(
                select(CertifiedStatementModel).where(CertifiedStatementModel.statement_id == statement_id)
            ).scalar_one_or_none()
            if row is None:
                return {"exists": False, "valid": False, "reason": "not_found"}

            computed_hash = hashlib.sha256(bytes(row.pdf_blob)).hexdigest()
            hash_ok = computed_hash == row.pdf_hash
            signature_ok = self._signer.verify_signature(row.pdf_hash, row.signature)
            valid = hash_ok and signature_ok
            metrics.record_statement_verification(status="success" if valid else "failed")

            return {
                "exists": True,
                "valid": valid,
                "statement_id": row.statement_id,
                "hash_ok": hash_ok,
                "signature_ok": signature_ok,
                "pdf_hash": row.pdf_hash,
                "computed_hash": computed_hash,
                "verification_url": row.verification_url,
            }

    @staticmethod
    def _resolve_period(period: str) -> tuple[str, date, date]:
        label = period.strip().lower()
        end_date = datetime.now(timezone.utc).date()
        if label == "3m":
            start_date = end_date - timedelta(days=90)
        elif label == "6m":
            start_date = end_date - timedelta(days=180)
        elif label == "12m":
            start_date = end_date - timedelta(days=365)
        else:
            raise ValueError("period must be one of: 3m, 6m, 12m")
        return label, start_date, end_date

    @staticmethod
    def _serialize(row: CertifiedStatementModel, *, idempotent: bool) -> dict:
        return {
            "statement_id": row.statement_id,
            "user_id": row.user_id,
            "merchant_name": row.merchant_name,
            "period": row.period_label,
            "period_start": row.period_start.isoformat(),
            "period_end": row.period_end.isoformat(),
            "total_sales": str(row.total_sales),
            "total_charges": str(row.total_charges),
            "net_result": str(row.net_result),
            "cashflow": str(row.cashflow),
            "statement_fee": str(row.statement_fee),
            "currency": row.currency,
            "pdf_hash": row.pdf_hash,
            "embedded_hash": row.embedded_hash,
            "signature": row.signature,
            "signature_algorithm": row.signature_algorithm,
            "signature_key_id": row.signature_key_id,
            "verification_url": row.verification_url,
            "immutable": bool(row.immutable),
            "idempotent": idempotent,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


statement_engine = StatementEngine()


def generate_statement(user_id: str, period: str, *, idempotency_key: str, merchant_name: str | None = None) -> dict:
    return statement_engine.generate_statement(user_id, period, idempotency_key=idempotency_key, merchant_name=merchant_name)
