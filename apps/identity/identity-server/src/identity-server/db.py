
from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

DEFAULT_SQLITE_URL = "sqlite:///./cast_identity.db"


class Base(DeclarativeBase):
    pass


def _db_url() -> str:
    return settings.DATABASE_URL or DEFAULT_SQLITE_URL


def _create_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, echo=False, future=True, connect_args={"check_same_thread": False})
    return create_engine(url, echo=False, future=True)

engine = _create_engine(_db_url())
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
