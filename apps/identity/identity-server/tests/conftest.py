
from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.db import Base
from app.api.deps import get_db
from app.main import app


@pytest.fixture(scope="session")
def db_engine():
    # Use a temp SQLite file (not in-memory, to support multiple connections)
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        os.remove(path)


@pytest.fixture
def db_session(db_engine) -> Generator:
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session) -> Generator:
    # Override dependency to use our test session
    def _get_db_for_test():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_for_test
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
