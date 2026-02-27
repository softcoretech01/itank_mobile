from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.regulations_master import RegulationsMaster
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class RegulationBase(BaseModel):
    regulation_name: str
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

class RegulationCreate(RegulationBase):
    pass

class RegulationUpdate(BaseModel):
    regulation_name: Optional[str] = None
    updated_by: Optional[int] = None

class RegulationOut(RegulationBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# --------------------------
# CRUD Endpoints
# --------------------------

@router.post("/", response_model=RegulationOut)
def create_regulation(data: RegulationCreate, db: Session = Depends(get_db)):
    existing = db.query(RegulationsMaster).filter_by(regulation_name=data.regulation_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Regulation already exists")

    new_reg = RegulationsMaster(
        regulation_name=data.regulation_name,
        created_by=data.created_by
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg


@router.get("/", response_model=List[RegulationOut])
def get_all_regulations(db: Session = Depends(get_db)):
    return db.query(RegulationsMaster).order_by(RegulationsMaster.id).all()


@router.get("/{reg_id}", response_model=RegulationOut)
def get_regulation(reg_id: int, db: Session = Depends(get_db)):
    reg = db.query(RegulationsMaster).filter_by(id=reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return reg


@router.put("/{reg_id}", response_model=RegulationOut)
def update_regulation(reg_id: int, data: RegulationUpdate, db: Session = Depends(get_db)):
    reg = db.query(RegulationsMaster).filter_by(id=reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")

    if data.regulation_name:
        reg.regulation_name = data.regulation_name
    if data.updated_by is not None:
        reg.updated_by = data.updated_by

    db.commit()
    db.refresh(reg)
    return reg


@router.delete("/{reg_id}")
def delete_regulation(reg_id: int, db: Session = Depends(get_db)):
    reg = db.query(RegulationsMaster).filter_by(id=reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")

    db.delete(reg)
    db.commit()
    return {"message": "Regulation deleted successfully"}
