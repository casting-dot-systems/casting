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

from identity_server.db import Base


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


class ApplicationIdentity(Base):
    """Identity mapping stored in the public schema."""

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

    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "application", name="uq_identity_entity_app"),
        Index("ix_identities_entity", "entity_type", "entity_id"),
        Index("ix_identities_application", "application"),
    )
