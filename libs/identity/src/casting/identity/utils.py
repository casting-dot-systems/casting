"""Utility functions for the identity module."""

from __future__ import annotations

from typing import Callable, TypeVar

from sqlalchemy.engine import Connection, Engine
from dotenv import load_dotenv


load_dotenv()

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
