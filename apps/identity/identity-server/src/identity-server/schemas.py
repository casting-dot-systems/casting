
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

EntityType = Literal["member", "meeting", "project"]


# ---------- Members ----------
class MemberBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str
    primary_email: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: Optional[str] = None
    primary_email: Optional[str] = None


class MemberRead(MemberBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------- Meetings ----------
class MeetingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None


class MeetingRead(MeetingBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------- Projects ----------
class ProjectBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(ProjectBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------- Application Identity ----------
class IdentityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: EntityType
    entity_id: uuid.UUID
    application: str = Field(description="Application name, e.g. email, notion, obsidian, discord, ...")
    external_id: str = Field(description="Application-specific identifier (email address, page ID, user/channel ID, ...)")
    display_name: Optional[str] = None
    uri: Optional[str] = Field(default=None, description="Optional deep link / URL")
    is_primary: bool = False
    metadata: Optional[Dict[str, Any]] = None


class IdentityCreate(IdentityBase):
    pass


class IdentityUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    application: Optional[str] = None
    external_id: Optional[str] = None
    display_name: Optional[str] = None
    uri: Optional[str] = None
    is_primary: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class IdentityRead(IdentityBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------- Resolver ----------
class ResolvedEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: EntityType
    entity: dict
    identities: list[IdentityRead]
