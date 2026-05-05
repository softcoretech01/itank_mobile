from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

from app.models.tank_inspection import TankInspection
from app.database import get_db

router = APIRouter()

# -----------------------------
# Pydantic Schemas
# -----------------------------
class TankInspectionBase(BaseModel):
    tank_id: Optional[int] = None
    insp_2_5y_date: Optional[date] = None # Expects date object
    next_insp_date: Optional[date] = None # Expects date object
    tank_certificate: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class TankInspectionCreate(TankInspectionBase):
    tank_id: int  # Make tank_id mandatory while creating

class TankInspectionUpdate(TankInspectionBase):
    pass

# --- This Pydantic model handles serialization for the frontend ---
class TankInspectionResponse(TankInspectionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------
# CRUD Operations
# -----------------------------

# CREATE
@router.post("/", response_model=TankInspectionResponse)
def create_tank_inspection(data: TankInspectionCreate, db: Session = Depends(get_db)):
    result = db.execute(
        text("CALL sp_CreateTankInspection(:tank_id, :insp_date, :next_date, :cert, :eid)"),
        {
            "tank_id": data.tank_id,
            "insp_date": data.insp_2_5y_date,
            "next_date": data.next_insp_date,
            "cert": data.tank_certificate,
            "eid": data.created_by or "System"
        }
    ).mappings().first()
    db.commit()
    return dict(result)


# READ ALL
@router.get("/", response_model=List[TankInspectionResponse])
def get_all_tank_inspections(db: Session = Depends(get_db)):
    results = db.execute(text("CALL sp_GetAllTankInspections()")).mappings().fetchall()
    return [dict(r) for r in results]


# READ BY ID
@router.get("/{id}", response_model=TankInspectionResponse)
def get_tank_inspection(id: int, db: Session = Depends(get_db)):
    record = db.execute(text("CALL sp_GetTankInspectionById(:id)"), {"id": id}).mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Tank inspection not found")
    return dict(record)


# UPDATE
@router.put("/{id}", response_model=TankInspectionResponse)
def update_tank_inspection(id: int, data: TankInspectionUpdate, db: Session = Depends(get_db)):
    existing = db.execute(text("CALL sp_GetTankInspectionById(:id)"), {"id": id}).mappings().first()
    if not existing:
        raise HTTPException(status_code=404, detail="Tank inspection not found")

    upd = dict(existing)
    for key, value in data.model_dump(exclude_unset=True).items():
        upd[key] = value

    result = db.execute(
        text("CALL sp_UpdateTankInspection(:id, :tank_id, :insp_date, :next_date, :cert, :eid)"),
        {
            "id": id,
            "tank_id": upd["tank_id"],
            "insp_date": upd["insp_2_5y_date"],
            "next_date": upd["next_insp_date"],
            "cert": upd["tank_certificate"],
            "eid": upd["updated_by"] or "System"
        }
    ).mappings().first()
    db.commit()
    return dict(result)


# DELETE
@router.delete("/{id}")
def delete_tank_inspection(id: int, db: Session = Depends(get_db)):
    record = db.execute(text("CALL sp_GetTankInspectionById(:id)"), {"id": id}).mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Tank inspection not found")

    db.execute(text("CALL sp_DeleteTankInspection(:id)"), {"id": id})
    db.commit()
    return {"detail": "Tank inspection deleted successfully"}