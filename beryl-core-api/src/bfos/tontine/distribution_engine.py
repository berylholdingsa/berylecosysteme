"""Contribution and distribution orchestration for BTSE cycles."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from src.bfos.fee_engine import FeeEngine, fee_engine
from src.bfos.tontine.escrow_wallet import EscrowWallet, escrow_wallet
from src.bfos.tontine.schedule_engine import calculate_next_distribution_date
from src.db.models.tontine import TontineCycleModel, TontineGroupModel
from src.observability.logging.logger import logger


class DistributionEngine:
    """Manages active cycle state and ledger-backed pool movements."""

    def __init__(self, *, fees: FeeEngine | None = None, wallet: EscrowWallet | None = None) -> None:
        self._fees = fees or fee_engine
        self._wallet = wallet or escrow_wallet

    def ensure_active_cycle(self, *, session, group: TontineGroupModel) -> TontineCycleModel:
        active = session.execute(
            select(TontineCycleModel)
            .where(
                TontineCycleModel.tontine_id == group.id,
                TontineCycleModel.status.in_(["ACTIVE", "PENDING"]),
            )
            .order_by(TontineCycleModel.cycle_number.desc())
        ).scalars().first()
        if active is not None:
            return active

        latest = session.execute(
            select(TontineCycleModel)
            .where(TontineCycleModel.tontine_id == group.id)
            .order_by(TontineCycleModel.cycle_number.desc())
        ).scalars().first()
        next_cycle = int(latest.cycle_number) + 1 if latest is not None else 1

        row = TontineCycleModel(
            tontine_id=group.id,
            cycle_number=next_cycle,
            total_pool=Decimal("0.00"),
            next_distribution_date=calculate_next_distribution_date(
                group.frequency_type,
                from_date=datetime.now(timezone.utc),
            ),
            status="ACTIVE",
            commission_total=Decimal("0.00"),
        )
        session.add(row)
        session.flush()
        return row

    def record_contribution(
        self,
        *,
        session,
        group: TontineGroupModel,
        user_id: str,
        amount: Decimal,
        actor_id: str,
        correlation_id: str,
        reference: str,
    ) -> dict:
        cycle = self.ensure_active_cycle(session=session, group=group)
        posting = self._wallet.record_contribution(
            session=session,
            tontine_id=str(group.id),
            user_id=user_id,
            amount=amount,
            reference=reference,
            actor_id=actor_id,
            correlation_id=correlation_id,
        )
        fee = self._fees.calculate_tontine_fee(
            amount,
            session=session,
            actor_id=actor_id,
            correlation_id=correlation_id,
            transaction_id=f"{reference}:fee",
            currency="XOF",
        ).fee_amount
        commission_posting = self._wallet.charge_commission(
            session=session,
            tontine_id=str(group.id),
            amount=fee,
            reference=f"{reference}:commission",
            actor_id=actor_id,
            correlation_id=correlation_id,
        )

        cycle.total_pool = (Decimal(str(cycle.total_pool)) + Decimal(str(amount)) - fee).quantize(Decimal("0.01"))
        cycle.commission_total = (Decimal(str(cycle.commission_total)) + fee).quantize(Decimal("0.01"))
        session.flush()

        logger.info(
            "event=tontine_contribution_recorded",
            tontine_id=str(group.id),
            user_id=user_id,
            amount=str(amount),
            fee=str(fee),
            cycle_number=str(cycle.cycle_number),
        )

        return {
            "cycle_id": str(cycle.id),
            "cycle_number": int(cycle.cycle_number),
            "total_pool": str(cycle.total_pool),
            "commission_total": str(cycle.commission_total),
            "next_distribution_date": cycle.next_distribution_date.isoformat(),
            "fee_amount": str(fee),
            "contribution_posting": posting,
            "commission_posting": commission_posting,
        }

    def record_distribution(
        self,
        *,
        session,
        group: TontineGroupModel,
        target_user_id: str,
        amount: Decimal,
        actor_id: str,
        correlation_id: str,
        reference: str,
    ) -> dict:
        cycle = self.ensure_active_cycle(session=session, group=group)
        balance = self._wallet.get_escrow_balance(session=session, tontine_id=str(group.id))
        normalized_amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        if normalized_amount <= 0:
            raise ValueError("distribution amount must be positive")
        if normalized_amount > balance:
            raise ValueError("insufficient tontine escrow balance")

        posting = self._wallet.record_distribution(
            session=session,
            tontine_id=str(group.id),
            target_user_id=target_user_id,
            amount=normalized_amount,
            reference=reference,
            actor_id=actor_id,
            correlation_id=correlation_id,
        )
        cycle.total_pool = (Decimal(str(cycle.total_pool)) - normalized_amount).quantize(Decimal("0.01"))
        cycle.next_distribution_date = calculate_next_distribution_date(
            group.frequency_type,
            from_date=datetime.now(timezone.utc),
        )
        if cycle.total_pool <= Decimal("0.00"):
            cycle.total_pool = Decimal("0.00")
            cycle.status = "COMPLETED"
        session.flush()

        logger.info(
            "event=tontine_distribution_recorded",
            tontine_id=str(group.id),
            target_user_id=target_user_id,
            amount=str(normalized_amount),
            cycle_number=str(cycle.cycle_number),
            cycle_status=cycle.status,
        )

        return {
            "cycle_id": str(cycle.id),
            "cycle_number": int(cycle.cycle_number),
            "distributed_amount": str(normalized_amount),
            "total_pool": str(cycle.total_pool),
            "next_distribution_date": cycle.next_distribution_date.isoformat(),
            "status": cycle.status,
            "posting": posting,
        }


distribution_engine = DistributionEngine()
