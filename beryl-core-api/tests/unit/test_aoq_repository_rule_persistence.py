"""Unit tests for AOQ rule persistence against SQLAlchemy models."""

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import src.api.v1.routes.aoq_routes as aoq_routes
from src.api.v1.schemas.aoq_schema import RuleSchema
from src.db.models.aoq import AoqRuleModel
from src.db.sqlalchemy import Base
from src.orchestration.aoq.repository import AoqRepository
from src.orchestration.aoq.service import AoqService


def test_create_rule_persists_weights_json(tmp_path: Path):
    db_path = tmp_path / "aoq_repo.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )
    Base.metadata.create_all(bind=engine, tables=[AoqRuleModel.__table__], checkfirst=True)

    repository = AoqRepository(session_factory=TestSessionLocal)
    created = repository.create_rule(
        {
            "name": "risk-v3",
            "threshold": 61.5,
            "weight_fintech": 0.4,
            "weight_mobility": 0.2,
            "weight_esg": 0.2,
            "weight_social": 0.2,
            "active": True,
        }
    )

    assert created.id is not None
    assert created.threshold == 61.5
    assert created.weights["fintech"] == 0.4
    assert created.weight_social == 0.2
    assert created.version == 1

    with TestSessionLocal() as session:
        persisted = session.execute(
            select(AoqRuleModel).where(AoqRuleModel.id == created.id)
        ).scalar_one()
        assert isinstance(persisted.weights, dict)
        assert persisted.weights == {
            "fintech": 0.4,
            "mobility": 0.2,
            "esg": 0.2,
            "social": 0.2,
        }


def test_create_rule_handler_persists_rule_in_db(tmp_path: Path):
    db_path = tmp_path / "aoq_api.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )
    Base.metadata.create_all(bind=engine, tables=[AoqRuleModel.__table__], checkfirst=True)

    repository = AoqRepository(session_factory=TestSessionLocal)

    class LocalAoqService(AoqService):
        def _init_aoq_tables(self) -> None:
            return None

    aoq_routes.service = LocalAoqService(repository=repository)

    payload = RuleSchema(
        name="risk-v4",
        threshold=62.0,
        weight_fintech=0.35,
        weight_mobility=0.25,
        weight_esg=0.25,
        weight_social=0.15,
        active=True,
    )
    response = aoq_routes.create_rule(payload)

    assert response.name == "risk-v4"
    assert response.weight_fintech == 0.35

    with TestSessionLocal() as session:
        persisted = session.execute(
            select(AoqRuleModel).where(AoqRuleModel.name == "risk-v4")
        ).scalar_one()
        assert persisted.threshold == 62.0
        assert persisted.weights["fintech"] == 0.35
