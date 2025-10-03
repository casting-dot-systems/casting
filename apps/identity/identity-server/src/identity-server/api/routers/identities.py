
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db
from app.crud import identities as crud


router = APIRouter(prefix="/identities", tags=["identities"])


@router.post("", response_model=schemas.IdentityRead, status_code=status.HTTP_201_CREATED)
def create_identity(payload: schemas.IdentityCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.get("/{id}", response_model=schemas.IdentityRead)
def get_identity(id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Identity not found")
    return obj


@router.get("", response_model=list[schemas.IdentityRead])
def list_identities(
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    application: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0),
    db: Session = Depends(get_db),
):
    return crud.list(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        application=application,
        skip=skip,
        limit=limit,
    )


@router.patch("/{id}", response_model=schemas.IdentityRead)
def update_identity(id: uuid.UUID, payload: schemas.IdentityUpdate, db: Session = Depends(get_db)):
    obj = crud.update(db, id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Identity not found")
    return obj


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_identity(id: uuid.UUID, db: Session = Depends(get_db)):
    ok = crud.delete(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Identity not found")
    return None
