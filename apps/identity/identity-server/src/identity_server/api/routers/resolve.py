
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from identity_server import schemas
from identity_server.api.deps import get_db
from identity_server.services.resolver import resolve as resolve_service
from identity_server.core.enums import EntityType

router = APIRouter(prefix="/resolve", tags=["resolve"])


@router.get("/{entity_type}/{entity_id}", response_model=schemas.ResolvedEntity)
def resolve(
    entity_type: EntityType,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Resolve an entity by returning its data and all application identities.

    This endpoint queries both catalog schema (for entity data)
    and public schema (for application-specific identities).
    """
    result = resolve_service(db, entity_type, entity_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result
