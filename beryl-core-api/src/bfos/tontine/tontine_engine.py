"""Main BTSE orchestration engine."""

from __future__ import annotations

import hashlib
import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from sqlalchemy import select

from src.bfos.tontine.aoq_tontine_engine import (
    adjust_reputation,
    detect_collusion,
    detect_default_risk,
    detect_schedule_manipulation,
    freeze_group_if_needed,
)
from src.bfos.tontine.distribution_engine import DistributionEngine, distribution_engine
from src.bfos.tontine.escrow_wallet import EscrowWallet, escrow_wallet
from src.bfos.tontine.schedule_engine import calculate_next_distribution_date, enforce_schedule_lock, validate_frequency
from src.bfos.tontine.security_code_manager import SecurityCodeManager, security_code_manager
from src.bfos.tontine.unanimous_withdrawal_engine import UnanimousWithdrawalEngine, unanimous_withdrawal_engine
from src.config.settings import settings
from src.core.audit import audit_service
from src.core.security import idempotency_service
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.tontine import (
    TontineCycleModel,
    TontineGroupModel,
    TontineMemberModel,
    TontineVoteModel,
    TontineWithdrawRequestModel,
)
from src.db.sqlalchemy import Base, SessionLocal, get_engine
from src.infrastructure.kafka.compliance.event_signature_verifier import event_signature_verifier
from src.observability.logging.logger import logger
from src.observability.metrics.prometheus import metrics


class TontineEngine:
    """Implements BTSE v1 with immutable controls and operational safety."""

    def __init__(
        self,
        *,
        session_factory: Callable = SessionLocal,
        wallet: EscrowWallet | None = None,
        distributions: DistributionEngine | None = None,
        unanimous: UnanimousWithdrawalEngine | None = None,
        codes: SecurityCodeManager | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._wallet = wallet or escrow_wallet
        self._distributions = distributions or distribution_engine
        self._unanimous = unanimous or unanimous_withdrawal_engine
        self._codes = codes or security_code_manager
        try:
            Base.metadata.create_all(
                bind=get_engine(),
                tables=[
                    IdempotencyKeyModel.__table__,
                    LedgerUserModel.__table__,
                    LedgerAccountModel.__table__,
                    LedgerEntryModel.__table__,
                    TontineGroupModel.__table__,
                    TontineMemberModel.__table__,
                    TontineCycleModel.__table__,
                    TontineWithdrawRequestModel.__table__,
                    TontineVoteModel.__table__,
                ],
                checkfirst=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(f"event=tontine_bootstrap_skipped reason={str(exc)}")

    @staticmethod
    def _parse_uuid(raw_id: str, field_name: str) -> uuid.UUID:
        try:
            return uuid.UUID(raw_id)
        except ValueError as exc:
            raise ValueError(f"invalid {field_name}") from exc

    @staticmethod
    def _normalize_amount(amount: Decimal) -> Decimal:
        normalized = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if normalized <= 0:
            raise ValueError("amount must be positive")
        return normalized

    @staticmethod
    def _build_reference(*parts: str) -> str:
        raw = ":".join(part.strip() for part in parts if part.strip())
        if len(raw) <= 128:
            return raw
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"tontine:{digest[:118]}"

    @staticmethod
    def _build_signature_hash(payload: dict) -> str:
        signed = dict(payload)
        signed["signature"] = event_signature_verifier.sign(payload)
        canonical = json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _load_group(self, *, session, tontine_id: str) -> TontineGroupModel:
        group_uuid = self._parse_uuid(tontine_id, "tontine_id")
        row = session.execute(select(TontineGroupModel).where(TontineGroupModel.id == group_uuid)).scalar_one_or_none()
        if row is None:
            raise ValueError("tontine not found")
        return row

    @staticmethod
    def _member_count(*, session, group_id: uuid.UUID) -> int:
        return len(
            list(
                session.execute(
                    select(TontineMemberModel.id).where(TontineMemberModel.tontine_id == group_id)
                ).scalars().all()
            )
        )

    def _assert_member(self, *, session, group_id: uuid.UUID, user_id: str) -> TontineMemberModel:
        row = session.execute(
            select(TontineMemberModel).where(
                TontineMemberModel.tontine_id == group_id,
                TontineMemberModel.user_id == user_id,
            )
        ).scalar_one_or_none()
        if row is None:
            raise ValueError("user is not a tontine member")
        return row

    @staticmethod
    def _latest_cycle(*, session, group_id: uuid.UUID) -> TontineCycleModel | None:
        return session.execute(
            select(TontineCycleModel)
            .where(TontineCycleModel.tontine_id == group_id)
            .order_by(TontineCycleModel.cycle_number.desc())
        ).scalars().first()

    def _average_reputation(self, *, session, group_id: uuid.UUID) -> Decimal:
        members = list(
            session.execute(
                select(TontineMemberModel).where(TontineMemberModel.tontine_id == group_id)
            ).scalars().all()
        )
        if not members:
            return Decimal("50.00")
        total = sum(Decimal(str(member.reputation_score)) for member in members)
        return (total / Decimal(str(len(members)))).quantize(Decimal("0.01"))

    def _serialize_group(self, *, session, group: TontineGroupModel, masked: bool) -> dict:
        cycle = self._latest_cycle(session=session, group_id=group.id)
        if cycle is None:
            next_distribution_date = calculate_next_distribution_date(
                group.frequency_type,
                from_date=group.created_at,
            )
            current_cycle_number = 0
        else:
            next_distribution_date = cycle.next_distribution_date
            current_cycle_number = int(cycle.cycle_number)

        balance = self._wallet.get_escrow_balance(session=session, tontine_id=str(group.id))
        return {
            "tontine_id": str(group.id),
            "community_group_id": group.community_group_id,
            "contribution_amount": str(Decimal(str(group.contribution_amount)).quantize(Decimal("0.01"))),
            "frequency_type": group.frequency_type,
            "next_distribution_date": next_distribution_date.isoformat() if next_distribution_date else None,
            "balance": str(balance),
            "status": group.status,
            "member_count": self._member_count(session=session, group_id=group.id),
            "max_members": int(group.max_members),
            "current_cycle_number": current_cycle_number,
            "masked": masked,
            "created_at": group.created_at.isoformat() if group.created_at else None,
        }

    @staticmethod
    def _claim_idempotency(*, session, idempotency_key: str, actor_id: str) -> None:
        if not idempotency_service.claim_or_reject(session=session, key=idempotency_key, user_id=actor_id[:128]):
            raise ValueError("duplicate idempotency key")

    def create_tontine(
        self,
        *,
        community_group_id: str,
        created_by: str,
        contribution_amount: Decimal,
        frequency_type: str,
        security_code: str,
        max_members: int,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        community_id = community_group_id.strip()
        if not community_id:
            raise ValueError("community_group_id is required")
        normalized_frequency = validate_frequency(frequency_type)
        normalized_amount = self._normalize_amount(contribution_amount)
        if max_members < 2 or max_members > settings.bfos_tontine_max_members:
            raise ValueError(f"max_members must be between 2 and {settings.bfos_tontine_max_members}")

        with self._session_factory() as session:
            with session.begin():
                self._claim_idempotency(session=session, idempotency_key=idempotency_key, actor_id=created_by)
                security_hash = self._codes.hash_security_code(security_code)
                signature_hash = self._build_signature_hash(
                    {
                        "community_group_id": community_id,
                        "contribution_amount": str(normalized_amount),
                        "frequency_type": normalized_frequency,
                        "max_members": max_members,
                        "created_by": created_by,
                    }
                )
                group = TontineGroupModel(
                    community_group_id=community_id,
                    contribution_amount=normalized_amount,
                    frequency_type=normalized_frequency,
                    max_members=max_members,
                    security_code_hash=security_hash,
                    status="ACTIVE",
                    signature_hash=signature_hash,
                )
                session.add(group)
                session.flush()

                session.add(
                    TontineMemberModel(
                        tontine_id=group.id,
                        user_id=created_by,
                        reputation_score=Decimal(str(settings.bfos_tontine_default_reputation_score)).quantize(Decimal("0.01")),
                    )
                )
                self._wallet.ensure_escrow_account(
                    session=session,
                    tontine_id=str(group.id),
                    currency=settings.bfos_tontine_currency,
                )

                audit_service.record_financial_event(
                    session=session,
                    actor_id=created_by,
                    action="TONTINE_GROUP_CREATED",
                    amount=normalized_amount,
                    currency=settings.bfos_tontine_currency,
                    correlation_id=correlation_id,
                    payload={
                        "tontine_id": str(group.id),
                        "community_group_id": community_id,
                        "frequency_type": normalized_frequency,
                        "max_members": max_members,
                        "signature_hash": signature_hash,
                    },
                )

                metrics.record_tontine_created(frequency_type=normalized_frequency)
                logger.info(
                    "event=tontine_group_created",
                    tontine_id=str(group.id),
                    community_group_id=community_id,
                    created_by=created_by,
                    frequency_type=normalized_frequency,
                    max_members=str(max_members),
                )
                return self._serialize_group(session=session, group=group, masked=True)

    def join_tontine(
        self,
        *,
        tontine_id: str,
        user_id: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        with self._session_factory() as session:
            with session.begin():
                self._claim_idempotency(session=session, idempotency_key=idempotency_key, actor_id=user_id)
                group = self._load_group(session=session, tontine_id=tontine_id)
                if group.status in {"FROZEN", "CLOSED"}:
                    raise ValueError("tontine group is not accepting new members")
                current_members = self._member_count(session=session, group_id=group.id)
                if current_members >= int(group.max_members):
                    raise ValueError("max members limit reached")

                existing = session.execute(
                    select(TontineMemberModel).where(
                        TontineMemberModel.tontine_id == group.id,
                        TontineMemberModel.user_id == user_id,
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    raise ValueError("member already joined")

                session.add(
                    TontineMemberModel(
                        tontine_id=group.id,
                        user_id=user_id,
                        reputation_score=Decimal(str(settings.bfos_tontine_default_reputation_score)).quantize(Decimal("0.01")),
                    )
                )
                session.flush()

                audit_service.record_financial_event(
                    session=session,
                    actor_id=user_id,
                    action="TONTINE_MEMBER_JOINED",
                    amount=Decimal("0.00"),
                    currency=settings.bfos_tontine_currency,
                    correlation_id=correlation_id,
                    payload={"tontine_id": str(group.id), "user_id": user_id},
                )
                return self._serialize_group(session=session, group=group, masked=True)

    def contribute(
        self,
        *,
        tontine_id: str,
        user_id: str,
        amount: Decimal | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        with self._session_factory() as session:
            with session.begin():
                self._claim_idempotency(session=session, idempotency_key=idempotency_key, actor_id=user_id)
                group = self._load_group(session=session, tontine_id=tontine_id)
                if group.status != "ACTIVE":
                    raise ValueError("tontine group is not active")

                member = self._assert_member(session=session, group_id=group.id, user_id=user_id)
                expected_amount = Decimal(str(group.contribution_amount)).quantize(Decimal("0.01"))
                normalized_amount = expected_amount if amount is None else self._normalize_amount(amount)
                if normalized_amount != expected_amount:
                    raise ValueError("contribution amount must match group contribution_amount")

                reference = self._build_reference("tontine", str(group.id), "contribution", user_id, idempotency_key)
                distribution = self._distributions.record_contribution(
                    session=session,
                    group=group,
                    user_id=user_id,
                    amount=normalized_amount,
                    actor_id=user_id,
                    correlation_id=correlation_id,
                    reference=reference,
                )

                member.reputation_score = adjust_reputation(
                    Decimal(str(member.reputation_score)),
                    "regular_payment",
                )
                avg_reputation = self._average_reputation(session=session, group_id=group.id)
                default_signal = detect_default_risk(
                    {
                        "avg_reputation": str(avg_reputation),
                        "missed_contributions": 0,
                    }
                )
                group.status = freeze_group_if_needed(group.status, [default_signal])
                if group.status == "FROZEN":
                    metrics.record_tontine_default(reason="aoq_default_risk")

                audit_service.record_financial_event(
                    session=session,
                    actor_id=user_id,
                    action="TONTINE_CONTRIBUTION_ACCEPTED",
                    amount=normalized_amount,
                    currency=settings.bfos_tontine_currency,
                    correlation_id=correlation_id,
                    payload={
                        "tontine_id": str(group.id),
                        "reference": reference,
                        "fee_amount": distribution["fee_amount"],
                        "cycle_id": distribution["cycle_id"],
                    },
                )

                metrics.record_tontine_contribution(
                    amount=float(normalized_amount),
                    currency=settings.bfos_tontine_currency,
                )
                snapshot = self._serialize_group(session=session, group=group, masked=True)
                snapshot["fee_amount"] = distribution["fee_amount"]
                snapshot["idempotent"] = False
                return snapshot

    def request_withdraw(
        self,
        *,
        tontine_id: str,
        requested_by: str,
        amount: Decimal,
        security_code: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        normalized_amount = self._normalize_amount(amount)
        with self._session_factory() as session:
            with session.begin():
                self._claim_idempotency(session=session, idempotency_key=idempotency_key, actor_id=requested_by)
                group = self._load_group(session=session, tontine_id=tontine_id)
                if group.status == "FROZEN":
                    raise ValueError("tontine group is frozen")
                self._assert_member(session=session, group_id=group.id, user_id=requested_by)
                if not self._codes.verify_security_code(security_code, group.security_code_hash):
                    raise ValueError("invalid security code")

                balance = self._wallet.get_escrow_balance(session=session, tontine_id=str(group.id))
                if normalized_amount > balance:
                    raise ValueError("insufficient tontine escrow balance")

                request_row = self._unanimous.create_withdraw_request(
                    session=session,
                    group=group,
                    requested_by=requested_by,
                    amount=normalized_amount,
                )
                audit_service.record_financial_event(
                    session=session,
                    actor_id=requested_by,
                    action="TONTINE_WITHDRAW_REQUEST_CREATED",
                    amount=normalized_amount,
                    currency=settings.bfos_tontine_currency,
                    correlation_id=correlation_id,
                    payload={
                        "tontine_id": str(group.id),
                        "withdraw_request_id": str(request_row.id),
                        "requested_by": requested_by,
                    },
                )
                snapshot = self._serialize_group(session=session, group=group, masked=False)
                snapshot["withdraw_request_id"] = str(request_row.id)
                snapshot["withdraw_status"] = request_row.status
                snapshot["idempotent"] = False
                return snapshot

    def vote_withdraw(
        self,
        *,
        tontine_id: str,
        withdraw_request_id: str,
        user_id: str,
        approved: bool,
        security_code: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        with self._session_factory() as session:
            with session.begin():
                self._claim_idempotency(session=session, idempotency_key=idempotency_key, actor_id=user_id)
                group = self._load_group(session=session, tontine_id=tontine_id)
                if group.status == "FROZEN":
                    raise ValueError("tontine group is frozen")
                member = self._assert_member(session=session, group_id=group.id, user_id=user_id)
                if not self._codes.verify_security_code(security_code, group.security_code_hash):
                    raise ValueError("invalid security code")

                reference = self._build_reference("tontine", str(group.id), "withdraw", withdraw_request_id)
                vote_result = self._unanimous.vote(
                    session=session,
                    group=group,
                    withdraw_request_id=withdraw_request_id,
                    user_id=user_id,
                    approved=approved,
                    actor_id=user_id,
                    correlation_id=correlation_id,
                    reference=reference,
                )

                member.reputation_score = adjust_reputation(
                    Decimal(str(member.reputation_score)),
                    "unanimous_approval" if approved else "unanimous_rejection",
                )

                if vote_result["status"] == "REJECTED":
                    metrics.record_tontine_unanimous_vote_failure()
                if vote_result.get("executed"):
                    distributed = Decimal(str(vote_result["distribution"]["distributed_amount"]))
                    metrics.record_tontine_distribution(
                        amount=float(distributed),
                        currency=settings.bfos_tontine_currency,
                    )

                collusion_signal = detect_collusion({"duplicate_votes": 0, "rapid_multi_votes": 0})
                default_signal = detect_default_risk(
                    {"avg_reputation": str(self._average_reputation(session=session, group_id=group.id)), "missed_contributions": 0}
                )
                group.status = freeze_group_if_needed(group.status, [collusion_signal, default_signal])
                if group.status == "FROZEN":
                    metrics.record_tontine_default(reason="aoq_freeze")

                audit_service.record_financial_event(
                    session=session,
                    actor_id=user_id,
                    action="TONTINE_WITHDRAW_VOTE",
                    amount=Decimal("0.00"),
                    currency=settings.bfos_tontine_currency,
                    correlation_id=correlation_id,
                    payload={
                        "tontine_id": str(group.id),
                        "withdraw_request_id": withdraw_request_id,
                        "user_id": user_id,
                        "approved": bool(approved),
                        "status": vote_result["status"],
                    },
                )

                snapshot = self._serialize_group(session=session, group=group, masked=False)
                snapshot.update(vote_result)
                snapshot["idempotent"] = False
                return snapshot

    def update_frequency(
        self,
        *,
        tontine_id: str,
        requested_frequency: str,
        actor_id: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        normalized_request = validate_frequency(requested_frequency)
        with self._session_factory() as session:
            rejection_error: ValueError | None = None
            snapshot: dict | None = None
            with session.begin():
                self._claim_idempotency(session=session, idempotency_key=idempotency_key, actor_id=actor_id)
                group = self._load_group(session=session, tontine_id=tontine_id)
                active_cycle = self._latest_cycle(session=session, group_id=group.id)
                cycle_active = active_cycle is not None and active_cycle.status in {"ACTIVE", "PENDING"}

                try:
                    enforce_schedule_lock(
                        stored_frequency=group.frequency_type,
                        requested_frequency=normalized_request,
                        cycle_active=cycle_active,
                    )
                except ValueError as exc:
                    metrics.record_tontine_schedule_violation()
                    schedule_signal = detect_schedule_manipulation(
                        {
                            "stored_frequency": group.frequency_type,
                            "requested_frequency": normalized_request,
                            "cycle_active": cycle_active,
                        }
                    )
                    group.status = freeze_group_if_needed(group.status, [schedule_signal])
                    if group.status == "FROZEN":
                        metrics.record_tontine_default(reason="schedule_manipulation")
                    audit_service.record_financial_event(
                        session=session,
                        actor_id=actor_id,
                        action="TONTINE_FREQUENCY_UPDATE_REJECTED",
                        amount=Decimal("0.00"),
                        currency=settings.bfos_tontine_currency,
                        correlation_id=correlation_id,
                        payload={
                            "tontine_id": str(group.id),
                            "stored_frequency": group.frequency_type,
                            "requested_frequency": normalized_request,
                            "cycle_active": cycle_active,
                        },
                    )
                    rejection_error = exc
                else:
                    group.frequency_type = normalized_request
                    audit_service.record_financial_event(
                        session=session,
                        actor_id=actor_id,
                        action="TONTINE_FREQUENCY_UPDATED",
                        amount=Decimal("0.00"),
                        currency=settings.bfos_tontine_currency,
                        correlation_id=correlation_id,
                        payload={
                            "tontine_id": str(group.id),
                            "frequency_type": normalized_request,
                        },
                    )
                snapshot = self._serialize_group(session=session, group=group, masked=True)

            if rejection_error is not None:
                raise rejection_error
            if snapshot is None:
                raise ValueError("unable to update tontine frequency")
            return snapshot

    def get_tontine(self, *, tontine_id: str, security_code: str | None = None) -> dict | None:
        with self._session_factory() as session:
            group_uuid = self._parse_uuid(tontine_id, "tontine_id")
            group = session.execute(select(TontineGroupModel).where(TontineGroupModel.id == group_uuid)).scalar_one_or_none()
            if group is None:
                return None
            masked = True
            if security_code:
                masked = not self._codes.verify_security_code(security_code, group.security_code_hash)
            return self._serialize_group(session=session, group=group, masked=masked)

    def get_wallet_balance(self, *, tontine_id: str, security_code: str | None = None) -> dict | None:
        snapshot = self.get_tontine(tontine_id=tontine_id, security_code=security_code)
        if snapshot is None:
            return None
        return {
            "tontine_id": snapshot["tontine_id"],
            "balance": snapshot["balance"],
            "frequency_type": snapshot["frequency_type"],
            "next_distribution_date": snapshot["next_distribution_date"],
            "masked": snapshot["masked"],
            "status": snapshot["status"],
        }


tontine_engine = TontineEngine()
