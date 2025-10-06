"""Utility functions for the identity module."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

from casting.platform.config import bootstrap_env, find_app_dir
from sqlalchemy.engine import Connection, Engine


APP_DIR = find_app_dir(__file__)
bootstrap_env(app_dir=APP_DIR)

T = TypeVar("T")


def with_connection(conn: Connection | Engine, fn: Callable[[Connection], T]) -> T:
    """
    Run a callable with a Connection, whether you passed an Engine or Connection.
    If an Engine is passed, this will open a transaction and commit it.
    """
    if isinstance(conn, Engine):
        with conn.begin() as c:
            return fn(c)
    else:
        return fn(conn)
