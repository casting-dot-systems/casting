"""Database schema management for the identity module."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from .utils import with_connection

DDL_CREATE_IDENTITY_TABLE = """
create schema if not exists application;

create table if not exists application.identity (
    identity_id    uuid primary key default gen_random_uuid(),
    member_id      uuid not null references catalog.members(member_id) on delete cascade,
    identity_type  text not null,
    identity_value text not null,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    unique (identity_type, identity_value)
);

-- helpful indices
create index if not exists idx_identity_member on application.identity (member_id);
create index if not exists idx_identity_type on application.identity (identity_type);
"""


def ensure_identity_table(conn: Connection | Engine) -> None:
    """
    Ensure the application.identity table exists. Safe to call repeatedly.

    Note: This only creates the identity table and assumes catalog.members already exists.
    We do not create or modify the members table.
    """
    with_connection(conn, lambda c: c.execute(text(DDL_CREATE_IDENTITY_TABLE)))
