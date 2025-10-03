
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional


from sqlalchemy import (
    String,
    DateTime,
    func,
    JSON,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, CHAR

from app.db import Base



def utcnow() -> datetime:
    return datetime.utcnow()


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.

    Stores as CHAR(36) and returns `uuid.UUID` in Python.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)


class Member(Base):

    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True, unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ApplicationIdentity(Base):
    __tablename__ = "application_identities"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    # Polymorphic reference to the true entity
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)

    # App specifics
    application: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: email, notion, discord, ...
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)  # ex: email address, page ID, user/channel ID
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    uri: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # ex: notion page url
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "application", name="uq_identity_entity_app"),
        Index("ix_identities_entity", "entity_type", "entity_id"),
        Index("ix_identities_application", "application"),
    )
