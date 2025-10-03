
from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.core.enums import EntityType


def _load_entity(db: Session, entity_type: EntityType, id: uuid.UUID) -> Optional[dict[str, Any]]:
    if entity_type == EntityType.member:
        obj = db.get(models.Member, id)
        return {"id": str(obj.id), "full_name": obj.full_name, "primary_email": obj.primary_email} if obj else None
    elif entity_type == EntityType.meeting:
        obj = db.get(models.Meeting, id)
        if not obj:
            return None
        return {
            "id": str(obj.id),
            "title": obj.title,
            "scheduled_start": obj.scheduled_start.isoformat() if obj.scheduled_start else None,
            "scheduled_end": obj.scheduled_end.isoformat() if obj.scheduled_end else None,
        }
    elif entity_type == EntityType.project:
        obj = db.get(models.Project, id)
        return {"id": str(obj.id), "name": obj.name, "description": obj.description} if obj else None
    else:
        return None


def resolve(db: Session, entity_type: EntityType, id: uuid.UUID) -> Optional[schemas.ResolvedEntity]:
    entity_data = _load_entity(db, entity_type, id)
    if entity_data is None:
        return None

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
