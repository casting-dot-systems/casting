
from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from identity_server import models, schemas
from identity_server.core.enums import EntityType


def _get_table_name(db: Session, base_name: str) -> str:
    """Get the appropriate table name based on dialect."""
    dialect = db.bind.dialect.name
    if dialect == "sqlite":
        # SQLite doesn't support schemas, use prefixed table names
        return f"catalog_{base_name}"
    else:
        # PostgreSQL uses schema.table notation
        return f"catalog.{base_name}"


def _load_entity(db: Session, entity_type: EntityType, id: uuid.UUID) -> Optional[dict[str, Any]]:
    """Load entity data from the catalog schema using raw SQL."""
    if entity_type == EntityType.member:
        table_name = _get_table_name(db, "members")
        result = db.execute(
            text(f"SELECT member_id, name, status FROM {table_name} WHERE member_id = :id"),
            {"id": str(id)}
        ).fetchone()
        if not result:
            return None
        return {"member_id": str(result.member_id), "name": result.name, "status": result.status}

    elif entity_type == EntityType.meeting:
        table_name = _get_table_name(db, "meetings")
        result = db.execute(
            text(f"SELECT id, title, scheduled_start, scheduled_end FROM {table_name} WHERE id = :id"),
            {"id": str(id)}
        ).fetchone()
        if not result:
            return None
        return {
            "id": str(result.id),
            "title": result.title,
            "scheduled_start": result.scheduled_start.isoformat() if result.scheduled_start else None,
            "scheduled_end": result.scheduled_end.isoformat() if result.scheduled_end else None,
        }

    elif entity_type == EntityType.project:
        table_name = _get_table_name(db, "projects")
        result = db.execute(
            text(f"SELECT id, name, description FROM {table_name} WHERE id = :id"),
            {"id": str(id)}
        ).fetchone()
        if not result:
            return None
        return {"id": str(result.id), "name": result.name, "description": result.description}

    else:
        return None


def resolve(db: Session, entity_type: EntityType, id: uuid.UUID) -> Optional[schemas.ResolvedEntity]:
    """
    Resolve an entity by fetching its data from catalog schema and its application identities.

    Args:
        db: Database session
        entity_type: Type of entity to resolve
        id: ID of the entity

    Returns:
        ResolvedEntity containing the entity data and all its application identities, or None if not found
    """
    # Fetch entity data from catalog schema using raw SQL
    entity_data = _load_entity(db, entity_type, id)
    if entity_data is None:
        return None

    # Fetch identities from public.application_identities table
    identities = (
        db.query(models.ApplicationIdentity)
        .filter(
            models.ApplicationIdentity.entity_type == entity_type.value,
            models.ApplicationIdentity.entity_id == id,
        )
        .order_by(models.ApplicationIdentity.created_at.asc())
        .all()
    )

    identities_out = [schemas.IdentityRead.model_validate(i) for i in identities]

    return schemas.ResolvedEntity(
        entity_type=entity_type.value, entity=entity_data, identities=identities_out
    )
