"""Convenience resolvers for specific identity types."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.engine import Connection, Engine

from .operations import get_member_from_identity
from .types import MemberWithIdentities


def get_member_from_discord_id(conn: Connection | Engine, discord_id: str) -> Optional[MemberWithIdentities]:
    """Resolve a member by Discord ID."""
    return get_member_from_identity(conn, "discord", discord_id)


def get_member_from_notion_id(conn: Connection | Engine, notion_id: str) -> Optional[MemberWithIdentities]:
    """Resolve a member by Notion ID."""
    return get_member_from_identity(conn, "notion", notion_id)


def get_member_from_work_email(
    conn: Connection | Engine,
    email: str,
    *,
    fallback_to_members_email: bool = True,
) -> Optional[MemberWithIdentities]:
    """
    Resolve by work_email identity.

    Note: Since the simplified schema doesn't include primary_email in members,
    fallback is not available and will always return None if no explicit
    identity mapping exists.
    """
    result = get_member_from_identity(conn, "work_email", email)
    if result or not fallback_to_members_email:
        return result

    # Fallback is not available in the simplified schema
    return None
