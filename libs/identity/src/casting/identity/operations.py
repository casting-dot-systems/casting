"""Core operations for identity management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from .schema import ensure_identity_table
from .types import MemberWithIdentities
from .utils import with_connection


def set_identity(
    conn: Connection | Engine,
    *,
    member_id: str,
    identity_type: str,
    identity_value: str,
) -> None:
    """
    Upsert an identity mapping for a member. If the (type, value) already
    exists, it will be reassigned to the provided member_id.
    """
    def _run(c: Connection) -> None:
        ensure_identity_table(c)
        c.execute(
            text(
                """
                insert into application.identity (member_id, identity_type, identity_value)
                values (:member_id, :type, :value)
                on conflict (identity_type, identity_value)
                do update set member_id = excluded.member_id, updated_at = now()
                """
            ),
            {"member_id": member_id, "type": identity_type, "value": identity_value},
        )

    with_connection(conn, _run)


def list_identities(
    conn: Connection | Engine, *, member_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List identities (optionally for a single member).
    """
    def _run(c: Connection) -> List[Dict[str, Any]]:
        ensure_identity_table(c)

        if member_id:
            q = text(
                """
                select identity_id, member_id, identity_type, identity_value, created_at, updated_at
                from application.identity
                where member_id = :member_id
                order by identity_type, identity_value
                """
            )
            rows = c.execute(q, {"member_id": member_id}).mappings().all()
        else:
            q = text(
                """
                select identity_id, member_id, identity_type, identity_value, created_at, updated_at
                from application.identity
                order by member_id, identity_type, identity_value
                """
            )
            rows = c.execute(q).mappings().all()

        return [dict(r) for r in rows]

    return with_connection(conn, _run)


def get_member_from_identity(
    conn: Connection | Engine, identity_type: str, identity_value: str
) -> Optional[MemberWithIdentities]:
    """
    Generic resolver by (identity_type, identity_value).

    Returns:
        {
          "member": {...full row from catalog.members...},
          "identities": [{"identity_type": "...", "identity_value": "..."}, ...]
        }
    """
    def _run(c: Connection) -> Optional[MemberWithIdentities]:
        ensure_identity_table(c)
        row = c.execute(
            text(
                """
                select m.*
                from catalog.members m
                join application.identity i
                  on i.member_id = m.member_id
                where i.identity_type = :type
                  and i.identity_value = :value
                limit 1
                """
            ),
            {"type": identity_type, "value": identity_value},
        ).mappings().first()

        if not row:
            return None

        return _materialize_member_with_identities(c, member_id=row["member_id"], member_row=dict(row))

    return with_connection(conn, _run)


def _materialize_member_with_identities(
    c: Connection, *, member_id: str, member_row: Optional[Dict[str, Any]] = None
) -> MemberWithIdentities:
    """Helper to build a member with all identities."""
    if member_row is None:
        member_row_result = c.execute(
            text(
                """
                select *
                from catalog.members
                where member_id = :member_id
                """
            ),
            {"member_id": member_id},
        ).mappings().first()
        if not member_row_result:
            raise RuntimeError("member disappeared during read")
        member_row = dict(member_row_result)

    identities = c.execute(
        text(
            """
            select identity_type, identity_value
            from application.identity
            where member_id = :member_id
            order by identity_type, identity_value
            """
        ),
        {"member_id": member_id},
    ).mappings().all()

    return {
        "member": member_row,
        "identities": [dict(row) for row in identities],
    }