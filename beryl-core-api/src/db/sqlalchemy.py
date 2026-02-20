"""SQLAlchemy bootstrap for persistent storage."""

import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.settings import settings


Base = declarative_base()


def get_database_url() -> str:
    if os.getenv("TESTING") == "1":
        return "sqlite+pysqlite:///:memory:"
    return os.getenv("DATABASE_URL") or settings.database_url


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(
        get_database_url(),
        future=True,
        echo=False,
        pool_pre_ping=True,
    )


def get_session_local():
    engine = get_engine()
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )


def SessionLocal():
    """Lazy session factory compatible with previous module exports."""
    return get_session_local()()
