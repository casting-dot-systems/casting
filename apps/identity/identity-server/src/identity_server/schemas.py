from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

EntityType = Literal["member", "meeting", "project"]


# ---------- Application Identity ----------
class IdentityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    entity_type: EntityType
    entity_id: uuid.UUID
    application: str = Field(description="Application name, e.g. email, notion, obsidian, discord, ...")
    external_id: str = Field(
        description="Application-specific identifier (email address, page ID, user/channel ID, ...)"
    )
    display_name: Optional[str] = None
    uri: Optional[str] = Field(default=None, description="Optional deep link / URL")
    is_primary: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="meta")


class IdentityCreate(IdentityBase):
    pass


class IdentityUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    application: Optional[str] = None
    external_id: Optional[str] = None
    display_name: Optional[str] = None
    uri: Optional[str] = None
    is_primary: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="meta")


class IdentityRead(IdentityBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------- Resolver ----------
class ResolvedEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: EntityType
    entity: dict  # Entity data from catalog schema (varies by entity_type)
    identities: list[IdentityRead]  # All application-specific identities for this entity
