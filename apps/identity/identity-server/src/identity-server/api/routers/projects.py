
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db
from app.crud import projects as crud


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.get("/{id}", response_model=schemas.ProjectRead)
def get_project(id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Project not found")
    return obj


@router.get("", response_model=list[schemas.ProjectRead])
def list_projects(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)):
    return crud.list(db, skip=skip, limit=limit)


@router.patch("/{id}", response_model=schemas.ProjectRead)
def update_project(id: uuid.UUID, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    obj = crud.update(db, id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Project not found")
    return obj


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: uuid.UUID, db: Session = Depends(get_db)):
    ok = crud.delete(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
