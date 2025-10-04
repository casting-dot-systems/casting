
from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from identity_server.core.config import settings


# Base class for all tables
class Base(DeclarativeBase):
    pass


def _create_engine(url: str):
    """Create SQLAlchemy engine with appropriate settings based on dialect."""
    if url.startswith("sqlite"):
        return create_engine(url, echo=False, future=True, connect_args={"check_same_thread": False})
    return create_engine(url, echo=False, future=True, pool_pre_ping=True)


# Single database engine
engine = _create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope():
    """Context manager for database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
