
from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from identity_server import models
from identity_server import schemas


def create(db: Session, data: schemas.IdentityCreate) -> models.ApplicationIdentity:
    obj = models.ApplicationIdentity(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        application=data.application,
        external_id=data.external_id,
        display_name=data.display_name,
        uri=data.uri,
        is_primary=data.is_primary,
        meta=data.metadata,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, id: uuid.UUID) -> Optional[models.ApplicationIdentity]:
    return db.get(models.ApplicationIdentity, id)


def list(
    db: Session,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    application: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.ApplicationIdentity]:
    q = db.query(models.ApplicationIdentity)
    if entity_type is not None:
        q = q.filter(models.ApplicationIdentity.entity_type == entity_type)
    if entity_id is not None:
        q = q.filter(models.ApplicationIdentity.entity_id == entity_id)
    if application is not None:
        q = q.filter(models.ApplicationIdentity.application == application)
    return q.order_by(models.ApplicationIdentity.created_at.asc()).offset(skip).limit(limit).all()


def update(db: Session, id: uuid.UUID, data: schemas.IdentityUpdate) -> Optional[models.ApplicationIdentity]:
    obj = get(db, id)
    if not obj:
        return None
    if data.application is not None:
        obj.application = data.application
    if data.external_id is not None:
        obj.external_id = data.external_id
    if data.display_name is not None:
        obj.display_name = data.display_name
    if data.uri is not None:
        obj.uri = data.uri
    if data.is_primary is not None:
        obj.is_primary = data.is_primary
    if data.metadata is not None:
        obj.meta = data.metadata
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, id: uuid.UUID) -> bool:
    obj = get(db, id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
