"""PostgreSQL integration test for AOQ rules creation endpoint."""

from uuid import uuid4

import pytest
from sqlalchemy import delete, text
from sqlalchemy.exc import SQLAlchemyError

from src.config.settings import settings
from src.db.models.aoq import AoqRuleModel
from src.db.sqlalchemy import SessionLocal


def _is_postgres_database() -> bool:
    return settings.database_url.startswith("postgresql")


def _postgres_is_reachable() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@pytest.mark.asyncio
async def test_post_aoq_rules_persists_in_postgres(async_client, valid_tokens):
    if not _is_postgres_database():
        pytest.skip("Skipping: DATABASE_URL is not PostgreSQL.")
    if not _postgres_is_reachable():
        pytest.skip("Skipping: PostgreSQL is not reachable from test environment.")

    unique_name = f"it-aoq-rule-{uuid4().hex[:12]}"
    payload = {
        "name": unique_name,
        "threshold": 63.0,
        "weight_fintech": 0.35,
        "weight_mobility": 0.25,
        "weight_esg": 0.25,
        "weight_social": 0.15,
        "active": True,
    }

    with SessionLocal() as session:
        session.execute(delete(AoqRuleModel).where(AoqRuleModel.name == unique_name))
        session.commit()

    response = await async_client.post(
        "/api/v1/aoq/rules",
        headers={"Authorization": valid_tokens["social"]},
        json=payload,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == unique_name
    assert body["threshold"] == 63.0
    assert body["weight_fintech"] == 0.35

    with SessionLocal() as session:
        persisted = session.query(AoqRuleModel).filter(AoqRuleModel.name == unique_name).one_or_none()
        assert persisted is not None
        assert persisted.weights == {
            "fintech": 0.35,
            "mobility": 0.25,
            "esg": 0.25,
            "social": 0.15,
        }
        session.execute(delete(AoqRuleModel).where(AoqRuleModel.name == unique_name))
        session.commit()
