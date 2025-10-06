from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi import Depends

from identity_server.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
