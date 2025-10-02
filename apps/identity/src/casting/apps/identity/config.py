"""Configuration management for the identity CLI."""

from __future__ import annotations

import os
from typing import Optional

import typer
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_engine_from_cli(db: Optional[str]) -> Engine:
    """Get database engine from CLI parameter or environment variable."""
    url = db or os.getenv("DATABASE_URL")
    if not url:
        raise typer.BadParameter(
            "No database URL provided. Set --db or the DATABASE_URL environment variable."
        )
    return create_engine(url, future=True)