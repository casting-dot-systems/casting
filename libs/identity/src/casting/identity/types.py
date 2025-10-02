"""Type definitions for the identity module."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class IdentityRow(TypedDict, total=False):
    """Represents a row from the application.identity table."""
    identity_id: str
    member_id: str
    identity_type: str
    identity_value: str
    created_at: Any
    updated_at: Any


class MemberWithIdentities(TypedDict, total=False):
    """Represents a member with all their associated identities."""
    member: Dict[str, Any]
    identities: List[Dict[str, str]]