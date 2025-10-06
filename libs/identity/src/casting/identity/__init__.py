"""Identity management library for Casting Systems."""

from .operations import get_member_from_identity, list_identities, set_identity
from .resolvers import (
    get_member_from_discord_id,
    get_member_from_notion_id,
    get_member_from_work_email,
)
from .schema import ensure_identity_table
from .types import IdentityRow, MemberWithIdentities

__all__ = [
    # Schema management
    "ensure_identity_table",
    # Core operations
    "set_identity",
    "list_identities",
    "get_member_from_identity",
    # Convenience resolvers
    "get_member_from_discord_id",
    "get_member_from_notion_id",
    "get_member_from_work_email",
    # Types
    "IdentityRow",
    "MemberWithIdentities",
]
