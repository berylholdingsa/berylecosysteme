from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.bfos.tontine.security_code_manager import SecurityCodeManager
from src.bfos.tontine.tontine_engine import TontineEngine
from src.db.models.audit_chain import AuditChainEventModel
from src.db.models.idempotency import IdempotencyKeyModel
from src.db.models.ledger import LedgerAccountModel, LedgerEntryModel, LedgerUserModel
from src.db.models.tontine import (
    TontineCycleModel,
    TontineGroupModel,
    TontineMemberModel,
    TontineVoteModel,
    TontineWithdrawRequestModel,
)
from src.db.sqlalchemy import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AuditChainEventModel.__table__,
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
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_security_code_is_hashed_and_verified() -> None:
    manager = SecurityCodeManager(pepper="unit-test-pepper")
    hashed = manager.hash_security_code("12345")
    assert "12345" not in hashed
    assert manager.verify_security_code("12345", hashed)
    assert not manager.verify_security_code("54321", hashed)


def test_group_never_persists_security_code_in_cleartext() -> None:
    factory = _session_factory()
    engine = TontineEngine(session_factory=factory, codes=SecurityCodeManager(pepper="unit-test-pepper-2"))
    created = engine.create_tontine(
        community_group_id="community-sec",
        created_by="member-sec",
        contribution_amount=Decimal("100.00"),
        frequency_type="MONTHLY",
        security_code="67890",
        max_members=5,
        idempotency_key="idem-create-sec",
        correlation_id="corr-create-sec",
    )

    with factory() as session:
        row = session.execute(
            select(TontineGroupModel).where(TontineGroupModel.id == uuid.UUID(created["tontine_id"]))
        ).scalar_one()

    assert row.security_code_hash != "67890"
    assert row.security_code_hash.startswith("pbkdf2_sha256$")
