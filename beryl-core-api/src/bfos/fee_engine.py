"""Centralized fee engine for BFOS monetization."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from uuid import uuid4

from src.bfos.aoq_hook import optimize_fee
from src.config.settings import settings
from src.core.audit import audit_service
from src.db.sqlalchemy import SessionLocal
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


@dataclass(frozen=True)
class FeeComputation:
    fee_type: str
    base_amount: Decimal
    fee_amount: Decimal
    rate: Decimal
    currency: str


class FeeEngine:
    """Computes regulated BFOS fees with mandatory audit logging."""

    def __init__(
        self,
        *,
        session_factory: Callable = SessionLocal,
        internal_transfer_rate: Decimal | None = None,
        diaspora_rate: Decimal | None = None,
        certified_statement_rate: Decimal | None = None,
        tontine_rate: Decimal | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._internal_transfer_rate = internal_transfer_rate or Decimal(str(settings.bfos_internal_transfer_fee_rate))
        self._diaspora_rate = diaspora_rate or Decimal(str(settings.bfos_diaspora_fee_rate))
        self._certified_statement_rate = certified_statement_rate or Decimal(str(settings.bfos_certified_statement_fee_rate))
        self._tontine_rate = tontine_rate or Decimal(str(settings.bfos_tontine_fee_rate))

    def calculate_internal_transfer_fee(self, amount: Decimal, **kwargs) -> FeeComputation:
        return self._calculate("internal_transfer", amount, self._internal_transfer_rate, **kwargs)

    def calculate_diaspora_fee(self, amount: Decimal, **kwargs) -> FeeComputation:
        return self._calculate("diaspora", amount, self._diaspora_rate, **kwargs)

    def calculate_certified_statement_fee(self, total_period_amount: Decimal, **kwargs) -> FeeComputation:
        return self._calculate("certified_statement", total_period_amount, self._certified_statement_rate, **kwargs)

    def calculate_tontine_fee(self, total_pool: Decimal, **kwargs) -> FeeComputation:
        return self._calculate("tontine", total_pool, self._tontine_rate, **kwargs)

    def _calculate(
        self,
        fee_type: str,
        amount: Decimal,
        rate: Decimal,
        *,
        session=None,
        actor_id: str = "bfos-fee-engine",
        currency: str = "XOF",
        correlation_id: str | None = None,
        transaction_id: str | None = None,
    ) -> FeeComputation:
        base_amount = Decimal(str(amount))
        if base_amount <= 0:
            raise ValueError("amount must be positive")

        aoq_profile = optimize_fee({"actor_id": actor_id, "fee_type": fee_type})
        multiplier = Decimal(str(aoq_profile.get("multiplier", Decimal("1.00"))))
        adjusted_rate = (rate * multiplier).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        fee_amount = (base_amount * adjusted_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        computation = FeeComputation(
            fee_type=fee_type,
            base_amount=base_amount,
            fee_amount=fee_amount,
            rate=adjusted_rate,
            currency=currency.upper(),
        )

        self._record_audit(
            computation=computation,
            session=session,
            actor_id=actor_id,
            correlation_id=correlation_id or str(uuid4()),
            transaction_id=transaction_id,
        )
        metrics.record_fee_collected(fee_type=fee_type, currency=computation.currency, amount=float(fee_amount))
        logger.info(
            "event=bfos_fee_computed",
            fee_type=fee_type,
            amount=str(base_amount),
            fee_amount=str(fee_amount),
            rate=str(adjusted_rate),
            currency=computation.currency,
        )
        return computation

    def _record_audit(
        self,
        *,
        computation: FeeComputation,
        session,
        actor_id: str,
        correlation_id: str,
        transaction_id: str | None,
    ) -> None:
        payload = {
            "fee_type": computation.fee_type,
            "base_amount": str(computation.base_amount),
            "fee_amount": str(computation.fee_amount),
            "rate": str(computation.rate),
            "transaction_id": transaction_id,
        }
        payload["signature"] = event_signature_verifier.sign(payload)

        if session is not None:
            audit_service.record_financial_event(
                session=session,
                actor_id=actor_id,
                action="BFOS_FEE_CALCULATED",
                amount=computation.fee_amount,
                currency=computation.currency,
                correlation_id=correlation_id,
                payload=payload,
            )
            return

        with self._session_factory() as own_session:
            with own_session.begin():
                audit_service.record_financial_event(
                    session=own_session,
                    actor_id=actor_id,
                    action="BFOS_FEE_CALCULATED",
                    amount=computation.fee_amount,
                    currency=computation.currency,
                    correlation_id=correlation_id,
                    payload=payload,
                )


fee_engine = FeeEngine()


def calculate_internal_transfer_fee(amount: Decimal, **kwargs) -> Decimal:
    return fee_engine.calculate_internal_transfer_fee(amount, **kwargs).fee_amount


def calculate_diaspora_fee(amount: Decimal, **kwargs) -> Decimal:
    return fee_engine.calculate_diaspora_fee(amount, **kwargs).fee_amount


def calculate_certified_statement_fee(total_period_amount: Decimal, **kwargs) -> Decimal:
    return fee_engine.calculate_certified_statement_fee(total_period_amount, **kwargs).fee_amount


def calculate_tontine_fee(total_pool: Decimal, **kwargs) -> Decimal:
    return fee_engine.calculate_tontine_fee(total_pool, **kwargs).fee_amount
