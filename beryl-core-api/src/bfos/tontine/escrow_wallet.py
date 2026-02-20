"""Escrow wallet operations backed by immutable double-entry ledger."""

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select

from src.config.settings import settings
from src.core.audit import audit_service
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.observability.logging.logger import logger


class EscrowWallet:
    """Isolated ledger wallet for each Tontine group."""

    @staticmethod
    def _stable_uuid(seed: str) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_URL, seed)

    def _ensure_ledger_account(self, *, session, user_ref: str, currency: str) -> uuid.UUID:
        normalized_ref = user_ref[:128]

        # Reuse existing ledger user by business key first to avoid unique collisions
        # with other engines that may derive a different UUID from the same firebase_uid.
        user_row = session.execute(
            select(LedgerUserModel).where(LedgerUserModel.firebase_uid == normalized_ref)
        ).scalar_one_or_none()
        if user_row is None:
            user_uuid = self._stable_uuid(f"ledger-user:{normalized_ref}")
            user_row = session.get(LedgerUserModel, user_uuid)
            if user_row is None:
                user_row = LedgerUserModel(id=user_uuid, firebase_uid=normalized_ref)
                session.add(user_row)

        existing_account = session.execute(
            select(LedgerAccountModel).where(
                LedgerAccountModel.user_id == user_row.id,
                LedgerAccountModel.currency == currency,
            )
        ).scalar_one_or_none()
        if existing_account is not None:
            return existing_account.id

        account_uuid = self._stable_uuid(f"ledger-account:{normalized_ref}:{currency}")
        account_row = session.get(LedgerAccountModel, account_uuid)
        if account_row is None:
            account_row = LedgerAccountModel(id=account_uuid, user_id=user_row.id, currency=currency)
            session.add(account_row)

        session.flush()
        return account_row.id

    def ensure_escrow_account(self, *, session, tontine_id: str, currency: str) -> uuid.UUID:
        return self._ensure_ledger_account(
            session=session,
            user_ref=f"tontine:{tontine_id}:escrow",
            currency=currency,
        )

    def ensure_member_wallet_account(self, *, session, user_id: str, currency: str) -> uuid.UUID:
        return self._ensure_ledger_account(
            session=session,
            user_ref=f"user:{user_id}:wallet",
            currency=currency,
        )

    def ensure_revenue_account(self, *, session, currency: str) -> uuid.UUID:
        return self._ensure_ledger_account(session=session, user_ref="bfos:revenue", currency=currency)

    @staticmethod
    def _post_double_entry(*, session, debit_account: uuid.UUID, credit_account: uuid.UUID, amount: Decimal, reference: str) -> tuple[str, str]:
        normalized = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        debit = LedgerEntryModel(account_id=debit_account, amount=normalized, direction="DEBIT", reference=reference)
        credit = LedgerEntryModel(account_id=credit_account, amount=normalized, direction="CREDIT", reference=reference)
        session.add(debit)
        session.add(credit)
        session.flush()
        return str(debit.id), str(credit.id)

    def record_contribution(
        self,
        *,
        session,
        tontine_id: str,
        user_id: str,
        amount: Decimal,
        reference: str,
        actor_id: str,
        correlation_id: str,
    ) -> dict:
        currency = settings.bfos_tontine_currency
        member_account = self.ensure_member_wallet_account(session=session, user_id=user_id, currency=currency)
        escrow_account = self.ensure_escrow_account(session=session, tontine_id=tontine_id, currency=currency)
        debit_id, credit_id = self._post_double_entry(
            session=session,
            debit_account=member_account,
            credit_account=escrow_account,
            amount=amount,
            reference=reference,
        )

        audit_service.record_financial_event(
            session=session,
            actor_id=actor_id,
            action="TONTINE_ESCROW_CONTRIBUTION",
            amount=Decimal(str(amount)),
            currency=currency,
            correlation_id=correlation_id,
            payload={
                "tontine_id": tontine_id,
                "user_id": user_id,
                "reference": reference,
                "debit_entry_id": debit_id,
                "credit_entry_id": credit_id,
            },
        )
        return {"debit_entry_id": debit_id, "credit_entry_id": credit_id}

    def charge_commission(
        self,
        *,
        session,
        tontine_id: str,
        amount: Decimal,
        reference: str,
        actor_id: str,
        correlation_id: str,
    ) -> dict:
        currency = settings.bfos_tontine_currency
        escrow_account = self.ensure_escrow_account(session=session, tontine_id=tontine_id, currency=currency)
        revenue_account = self.ensure_revenue_account(session=session, currency=currency)
        debit_id, credit_id = self._post_double_entry(
            session=session,
            debit_account=escrow_account,
            credit_account=revenue_account,
            amount=amount,
            reference=reference,
        )
        audit_service.record_financial_event(
            session=session,
            actor_id=actor_id,
            action="TONTINE_ESCROW_COMMISSION",
            amount=Decimal(str(amount)),
            currency=currency,
            correlation_id=correlation_id,
            payload={
                "tontine_id": tontine_id,
                "reference": reference,
                "debit_entry_id": debit_id,
                "credit_entry_id": credit_id,
            },
        )
        return {"debit_entry_id": debit_id, "credit_entry_id": credit_id}

    def record_distribution(
        self,
        *,
        session,
        tontine_id: str,
        target_user_id: str,
        amount: Decimal,
        reference: str,
        actor_id: str,
        correlation_id: str,
    ) -> dict:
        currency = settings.bfos_tontine_currency
        escrow_account = self.ensure_escrow_account(session=session, tontine_id=tontine_id, currency=currency)
        target_account = self.ensure_member_wallet_account(session=session, user_id=target_user_id, currency=currency)
        debit_id, credit_id = self._post_double_entry(
            session=session,
            debit_account=escrow_account,
            credit_account=target_account,
            amount=amount,
            reference=reference,
        )
        audit_service.record_financial_event(
            session=session,
            actor_id=actor_id,
            action="TONTINE_ESCROW_DISTRIBUTION",
            amount=Decimal(str(amount)),
            currency=currency,
            correlation_id=correlation_id,
            payload={
                "tontine_id": tontine_id,
                "target_user_id": target_user_id,
                "reference": reference,
                "debit_entry_id": debit_id,
                "credit_entry_id": credit_id,
            },
        )
        return {"debit_entry_id": debit_id, "credit_entry_id": credit_id}

    def get_escrow_balance(self, *, session, tontine_id: str) -> Decimal:
        currency = settings.bfos_tontine_currency
        escrow_account = self.ensure_escrow_account(session=session, tontine_id=tontine_id, currency=currency)
        credit_total = session.execute(
            select(func.coalesce(func.sum(LedgerEntryModel.amount), 0)).where(
                LedgerEntryModel.account_id == escrow_account,
                LedgerEntryModel.direction == "CREDIT",
            )
        ).scalar_one()
        debit_total = session.execute(
            select(func.coalesce(func.sum(LedgerEntryModel.amount), 0)).where(
                LedgerEntryModel.account_id == escrow_account,
                LedgerEntryModel.direction == "DEBIT",
            )
        ).scalar_one()
        balance = (Decimal(str(credit_total)) - Decimal(str(debit_total))).quantize(Decimal("0.01"))
        logger.info("event=tontine_escrow_balance_computed", tontine_id=tontine_id, balance=str(balance))
        return balance


escrow_wallet = EscrowWallet()
