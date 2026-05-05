from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.tankcode_iso_master_model import TankCodeISOMaster
from app.routers.tank_inspection_router import get_current_user, success_resp, error_resp

router = APIRouter(prefix="/api/tank_code_master", tags=["tank_code_master"])

class TankCodeISOCreate(BaseModel):
    tankcode_iso: str

class TankCodeISOUpdate(BaseModel):
    tankcode_iso: Optional[str] = None
    status: Optional[int] = None

@router.get("/")
def get_all_tank_codes(db: Session = Depends(get_db)):
    try:
        results = db.execute(text("CALL sp_GetAllTankCodes()")).mappings().fetchall()
        return success_resp("Tank ISO codes fetched successfully", [dict(r) for r in results])
    except Exception as e:
        return error_resp(f"Error fetching tank ISO codes: {str(e)}", 500)

@router.get("/{id}")
def get_tank_code_by_id(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("CALL sp_GetTankCodeById(:id)"), {"id": id}).mappings().first()
        if not result:
            return error_resp("Tank ISO code not found", 404)
        return success_resp("Tank ISO code fetched successfully", dict(result))
    except Exception as e:
        return error_resp(f"Error fetching tank ISO code: {str(e)}", 500)

@router.post("/")
def create_tank_code(
    data: TankCodeISOCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        # Check if already exists using inline query for simplicity or we could add an SP for this
        eb = db.execute(text("SELECT id FROM tankcode_iso_master WHERE tankcode_iso = :code LIMIT 1"), {"code": data.tankcode_iso}).mappings().first()
        if eb:
            return error_resp(f"Tank ISO code '{data.tankcode_iso}' already exists", 400)

        emp_id = str(getattr(current_user, "emp_id", ""))
        
        result = db.execute(
            text("CALL sp_CreateTankCode(:code, :eid)"),
            {"code": data.tankcode_iso, "eid": emp_id}
        ).mappings().first()
        
        db.commit()
        return success_resp("Tank ISO code created successfully", dict(result), 201)
    except Exception as e:
        db.rollback()
        return error_resp(f"Error creating tank ISO code: {str(e)}", 500)

@router.put("/{id}")
def update_tank_code(
    id: int, 
    data: TankCodeISOUpdate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        existing = db.execute(text("CALL sp_GetTankCodeById(:id)"), {"id": id}).mappings().first()
        if not existing:
            return error_resp("Tank ISO code not found", 404)

        if data.tankcode_iso is not None and data.tankcode_iso != existing["tankcode_iso"]:
            eb = db.execute(text("SELECT id FROM tankcode_iso_master WHERE tankcode_iso = :code AND id <> :id LIMIT 1"), {"code": data.tankcode_iso, "id": id}).mappings().first()
            if eb:
                return error_resp(f"Tank ISO code '{data.tankcode_iso}' already exists", 400)

        emp_id = str(getattr(current_user, "emp_id", ""))
        
        result = db.execute(
            text("CALL sp_UpdateTankCode(:id, :code, :stat, :eid)"),
            {
                "id": id,
                "code": data.tankcode_iso,
                "stat": data.status,
                "eid": emp_id
            }
        ).mappings().first()
        
        db.commit()
        return success_resp("Tank ISO code updated successfully", dict(result))
    except Exception as e:
        db.rollback()
        return error_resp(f"Error updating tank ISO code: {str(e)}", 500)
