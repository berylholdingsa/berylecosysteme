"""Merchant accounting aggregation and financial summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Callable

from sqlalchemy import select

from src.bfos.accounting.aoq_accounting_hook import categorize_transaction, risk_signal, suggest_cashflow_improvement
from src.core.audit import audit_service
from src.db.models.fintech import FintechTransactionModel
from src.db.sqlalchemy import Base, SessionLocal, get_engine
from src.observability.logging.logger import logger


@dataclass(frozen=True)
class AggregatedTransaction:
    transaction_id: str
    actor_id: str
    amount: Decimal
    currency: str
    status: str
    target_account: str
    created_at: datetime
    category: str


class MerchantAccountingEngine:
    """Read-only accounting computation for merchants."""

    def __init__(self, *, session_factory: Callable = SessionLocal) -> None:
        self._session_factory = session_factory
        try:
            Base.metadata.create_all(bind=get_engine(), tables=[FintechTransactionModel.__table__], checkfirst=True)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=bfos_accounting_bootstrap_skipped reason={str(exc)}")

    def aggregate_transactions(self, user_id: str, start_date: date, end_date: date) -> dict:
        if end_date < start_date:
            raise ValueError("end_date must be greater than or equal to start_date")

        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)

        with self._session_factory() as session:
            rows = list(
                session.execute(
                    select(FintechTransactionModel).where(
                        FintechTransactionModel.actor_id == user_id,
                        FintechTransactionModel.created_at >= start_dt,
                        FintechTransactionModel.created_at <= end_dt,
                    )
                ).scalars().all()
            )

            aggregated = [
                AggregatedTransaction(
                    transaction_id=str(row.id),
                    actor_id=row.actor_id,
                    amount=Decimal(str(row.amount)),
                    currency=row.currency,
                    status=row.status,
                    target_account=row.target_account,
                    created_at=row.created_at,
                    category=categorize_transaction(
                        {
                            "status": row.status,
                            "target_account": row.target_account,
                            "amount": str(row.amount),
                        }
                    ),
                )
                for row in rows
            ]

            summary = self.calculate_financial_summary([asdict(tx) for tx in aggregated])
            cashflow = self.compute_cashflow([asdict(tx) for tx in aggregated])
            suggestion = suggest_cashflow_improvement(summary)
            risk = risk_signal(summary)

            context = session.begin_nested() if session.in_transaction() else session.begin()
            with context:
                audit_service.record_financial_event(
                    session=session,
                    actor_id=user_id,
                    action="BFOS_MERCHANT_ACCOUNTING_AGGREGATED",
                    amount=summary["total_sales"],
                    currency=summary["currency"],
                    correlation_id=f"acct-{user_id}-{start_date.isoformat()}-{end_date.isoformat()}",
                    payload={
                        "user_id": user_id,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "transaction_count": len(aggregated),
                        "summary": {k: str(v) for k, v in summary.items()},
                        "cashflow": {k: str(v) for k, v in cashflow.items()},
                    },
                )

        result = {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "transaction_count": len(aggregated),
            "transactions": [asdict(tx) for tx in aggregated],
            "summary": summary,
            "cashflow": cashflow,
            "aoq_suggestion": suggestion,
            "aoq_risk": risk,
        }

        logger.info(
            "event=bfos_accounting_aggregated",
            user_id=user_id,
            transaction_count=str(len(aggregated)),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        return result

    def calculate_financial_summary(self, data: list[dict]) -> dict:
        currency = "XOF"
        total_sales = Decimal("0.00")
        total_charges = Decimal("0.00")

        for tx in data:
            currency = str(tx.get("currency", currency)).upper()
            amount = Decimal(str(tx.get("amount", "0")))
            category = str(tx.get("category", "sale"))
            status = str(tx.get("status", "ACCEPTED")).upper()

            if status == "FAILED" or category == "ignored":
                continue

            if category == "charge":
                total_charges += abs(amount)
            else:
                total_sales += abs(amount)

        net_result = total_sales - total_charges
        return {
            "total_sales": total_sales.quantize(Decimal("0.01")),
            "total_charges": total_charges.quantize(Decimal("0.01")),
            "net_result": net_result.quantize(Decimal("0.01")),
            "currency": currency,
        }

    def compute_cashflow(self, data: list[dict]) -> dict:
        inflow = Decimal("0.00")
        outflow = Decimal("0.00")

        for tx in data:
            amount = Decimal(str(tx.get("amount", "0")))
            category = str(tx.get("category", "sale"))
            status = str(tx.get("status", "ACCEPTED")).upper()

            if status == "FAILED" or category == "ignored":
                continue

            if category == "charge":
                outflow += abs(amount)
            else:
                inflow += abs(amount)

        return {
            "inflow": inflow.quantize(Decimal("0.01")),
            "outflow": outflow.quantize(Decimal("0.01")),
            "net_cashflow": (inflow - outflow).quantize(Decimal("0.01")),
        }


merchant_accounting_engine = MerchantAccountingEngine()
