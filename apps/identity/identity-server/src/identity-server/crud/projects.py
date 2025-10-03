
from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app import models
from app import schemas


def create(db: Session, data: schemas.ProjectCreate) -> models.Project:
    obj = models.Project(name=data.name, description=data.description)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, id: uuid.UUID) -> Optional[models.Project]:
    return db.get(models.Project, id)


def list(db: Session, skip: int = 0, limit: int = 100) -> list[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()


def update(db: Session, id: uuid.UUID, data: schemas.ProjectUpdate) -> Optional[models.Project]:
    obj = get(db, id)
    if not obj:
        return None
    if data.name is not None:
        obj.name = data.name
    if data.description is not None:
        obj.description = data.description
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
