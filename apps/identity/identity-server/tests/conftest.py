from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from identity_server.db import Base
from identity_server.api.deps import get_db
from identity_server.main import app


@pytest.fixture(scope="session")
def db_engine():
    """Create a test database with catalog schema and tables."""
    # Use a temp SQLite file (not in-memory, to support multiple connections)
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})

    # Create catalog schema (SQLite doesn't support schemas, so we use table prefixes)
    # We'll create tables that match the catalog schema structure
    with engine.connect() as conn:
        # Create catalog_members table
        conn.execute(
            text("""
            CREATE TABLE catalog_members (
                member_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        # Create catalog_meetings table
        conn.execute(
            text("""
            CREATE TABLE catalog_meetings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                scheduled_start TIMESTAMP,
                scheduled_end TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        # Create catalog_projects table
        conn.execute(
            text("""
            CREATE TABLE catalog_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        conn.commit()

    # Create application_identities table (public schema)
    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        os.remove(path)


@pytest.fixture
def db_session(db_engine) -> Generator:
    """Create a database session for tests."""
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client with database dependency override."""

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
