
from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app import models
from app import schemas


def create(db: Session, data: schemas.MemberCreate) -> models.Member:
    obj = models.Member(full_name=data.full_name, primary_email=data.primary_email)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, id: uuid.UUID) -> Optional[models.Member]:
    return db.get(models.Member, id)


def list(db: Session, skip: int = 0, limit: int = 100) -> list[models.Member]:
    return db.query(models.Member).offset(skip).limit(limit).all()


def update(db: Session, id: uuid.UUID, data: schemas.MemberUpdate) -> Optional[models.Member]:
    obj = get(db, id)
    if not obj:
        return None
    if data.full_name is not None:
        obj.full_name = data.full_name
    if data.primary_email is not None:
        obj.primary_email = data.primary_email
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
