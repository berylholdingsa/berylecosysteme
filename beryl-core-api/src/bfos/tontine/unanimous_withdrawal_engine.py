"""Unanimous withdrawal workflow for Tontine escrow releases."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select

from src.bfos.tontine.distribution_engine import DistributionEngine, distribution_engine
from src.db.models.tontine import (
    TontineGroupModel,
    TontineMemberModel,
    TontineVoteModel,
    TontineWithdrawRequestModel,
)
from src.observability.logging.logger import logger


class UnanimousWithdrawalEngine:
    """Handle withdraw request lifecycle requiring 100% member approval."""

    def __init__(self, *, distributions: DistributionEngine | None = None) -> None:
        self._distributions = distributions or distribution_engine

    @staticmethod
    def _parse_uuid(raw_id: str, field_name: str) -> uuid.UUID:
        try:
            return uuid.UUID(raw_id)
        except ValueError as exc:
            raise ValueError(f"invalid {field_name}") from exc

    def create_withdraw_request(
        self,
        *,
        session,
        group: TontineGroupModel,
        requested_by: str,
        amount: Decimal,
    ) -> TontineWithdrawRequestModel:
        membership = session.execute(
            select(TontineMemberModel).where(
                TontineMemberModel.tontine_id == group.id,
                TontineMemberModel.user_id == requested_by,
            )
        ).scalar_one_or_none()
        if membership is None:
            raise ValueError("requester is not a tontine member")

        row = TontineWithdrawRequestModel(
            tontine_id=group.id,
            requested_by=requested_by,
            amount=Decimal(str(amount)).quantize(Decimal("0.01")),
            status="PENDING",
        )
        session.add(row)
        session.flush()
        logger.info(
            "event=tontine_withdraw_request_created",
            tontine_id=str(group.id),
            withdraw_request_id=str(row.id),
            requested_by=requested_by,
            amount=str(row.amount),
        )
        return row

    def vote(
        self,
        *,
        session,
        group: TontineGroupModel,
        withdraw_request_id: str,
        user_id: str,
        approved: bool,
        actor_id: str,
        correlation_id: str,
        reference: str,
    ) -> dict:
        request_uuid = self._parse_uuid(withdraw_request_id, "withdraw_request_id")
        request_row = session.execute(
            select(TontineWithdrawRequestModel).where(
                TontineWithdrawRequestModel.id == request_uuid,
                TontineWithdrawRequestModel.tontine_id == group.id,
            )
        ).scalar_one_or_none()
        if request_row is None:
            raise ValueError("withdraw request not found")

        if request_row.status in {"REJECTED", "EXECUTED"}:
            return {
                "withdraw_request_id": str(request_row.id),
                "status": request_row.status,
                "approved": False,
                "executed": request_row.status == "EXECUTED",
            }

        membership = session.execute(
            select(TontineMemberModel).where(
                TontineMemberModel.tontine_id == group.id,
                TontineMemberModel.user_id == user_id,
            )
        ).scalar_one_or_none()
        if membership is None:
            raise ValueError("voter is not a tontine member")

        existing_vote = session.execute(
            select(TontineVoteModel).where(
                TontineVoteModel.withdraw_request_id == request_uuid,
                TontineVoteModel.user_id == user_id,
            )
        ).scalar_one_or_none()
        if existing_vote is not None:
            raise ValueError("vote already cast for this user")

        vote_row = TontineVoteModel(
            tontine_id=group.id,
            withdraw_request_id=request_uuid,
            user_id=user_id,
            approved=bool(approved),
        )
        session.add(vote_row)
        session.flush()

        votes = list(
            session.execute(
                select(TontineVoteModel).where(TontineVoteModel.withdraw_request_id == request_uuid)
            ).scalars().all()
        )
        member_count = len(
            list(
                session.execute(
                    select(TontineMemberModel.id).where(TontineMemberModel.tontine_id == group.id)
                ).scalars().all()
            )
        )
        vote_count = len(votes)
        all_approved = all(bool(vote.approved) for vote in votes)
        has_rejection = any(not bool(vote.approved) for vote in votes)

        executed = False
        distribution_result = None
        if has_rejection:
            request_row.status = "REJECTED"
        elif vote_count >= member_count and all_approved:
            request_row.status = "APPROVED"
            distribution_result = self._distributions.record_distribution(
                session=session,
                group=group,
                target_user_id=request_row.requested_by,
                amount=Decimal(str(request_row.amount)),
                actor_id=actor_id,
                correlation_id=correlation_id,
                reference=reference,
            )
            request_row.status = "EXECUTED"
            executed = True
        else:
            request_row.status = "PENDING"

        session.flush()
        logger.info(
            "event=tontine_withdraw_vote_processed",
            tontine_id=str(group.id),
            withdraw_request_id=str(request_row.id),
            user_id=user_id,
            approved=str(bool(approved)),
            status=request_row.status,
            vote_count=str(vote_count),
            member_count=str(member_count),
        )
        return {
            "withdraw_request_id": str(request_row.id),
            "status": request_row.status,
            "approved": bool(approved),
            "vote_count": vote_count,
            "member_count": member_count,
            "executed": executed,
            "distribution": distribution_result,
        }


unanimous_withdrawal_engine = UnanimousWithdrawalEngine()
