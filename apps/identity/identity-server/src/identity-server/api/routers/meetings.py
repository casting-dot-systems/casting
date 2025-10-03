
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db
from app.crud import meetings as crud


router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=schemas.MeetingRead, status_code=status.HTTP_201_CREATED)
def create_meeting(payload: schemas.MeetingCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.get("/{id}", response_model=schemas.MeetingRead)
def get_meeting(id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return obj


@router.get("", response_model=list[schemas.MeetingRead])
def list_meetings(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)):
    return crud.list(db, skip=skip, limit=limit)


@router.patch("/{id}", response_model=schemas.MeetingRead)
def update_meeting(id: uuid.UUID, payload: schemas.MeetingUpdate, db: Session = Depends(get_db)):
    obj = crud.update(db, id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return obj


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(id: uuid.UUID, db: Session = Depends(get_db)):
    ok = crud.delete(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return None
