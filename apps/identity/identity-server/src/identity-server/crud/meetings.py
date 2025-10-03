
from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app import models
from app import schemas


def create(db: Session, data: schemas.MeetingCreate) -> models.Meeting:
    obj = models.Meeting(
        title=data.title, scheduled_start=data.scheduled_start, scheduled_end=data.scheduled_end
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, id: uuid.UUID) -> Optional[models.Meeting]:
    return db.get(models.Meeting, id)


def list(db: Session, skip: int = 0, limit: int = 100) -> list[models.Meeting]:
    return db.query(models.Meeting).offset(skip).limit(limit).all()


def update(db: Session, id: uuid.UUID, data: schemas.MeetingUpdate) -> Optional[models.Meeting]:
    obj = get(db, id)
    if not obj:
        return None
    if data.title is not None:
        obj.title = data.title
    if data.scheduled_start is not None:
        obj.scheduled_start = data.scheduled_start
    if data.scheduled_end is not None:
        obj.scheduled_end = data.scheduled_end
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
