from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
        codes = db.query(TankCodeISOMaster).all()
        return success_resp("Tank ISO codes fetched successfully", codes)
    except Exception as e:
        return error_resp(f"Error fetching tank ISO codes: {str(e)}", 500)

@router.get("/{id}")
def get_tank_code_by_id(id: int, db: Session = Depends(get_db)):
    try:
        code = db.query(TankCodeISOMaster).filter(TankCodeISOMaster.id == id).first()
        if not code:
            return error_resp("Tank ISO code not found", 404)
        return success_resp("Tank ISO code fetched successfully", code)
    except Exception as e:
        return error_resp(f"Error fetching tank ISO code: {str(e)}", 500)

@router.post("/")
def create_tank_code(
    data: TankCodeISOCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        # Check if already exists
        eb = db.query(TankCodeISOMaster).filter(TankCodeISOMaster.tankcode_iso == data.tankcode_iso).first()
        if eb:
            return error_resp(f"Tank ISO code '{data.tankcode_iso}' already exists", 400)

        emp_id = str(getattr(current_user, "emp_id", ""))
        
        new_code = TankCodeISOMaster(
            tankcode_iso=data.tankcode_iso,
            status=1,
            created_by=emp_id,
            modified_by=emp_id
        )
        db.add(new_code)
        db.commit()
        db.refresh(new_code)
        
        return success_resp("Tank ISO code created successfully", new_code, 201)
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
        code = db.query(TankCodeISOMaster).filter(TankCodeISOMaster.id == id).first()
        if not code:
            return error_resp("Tank ISO code not found", 404)

        if data.tankcode_iso is not None:
            # Check unique if changing
            if data.tankcode_iso != code.tankcode_iso:
                eb = db.query(TankCodeISOMaster).filter(TankCodeISOMaster.tankcode_iso == data.tankcode_iso).first()
                if eb:
                    return error_resp(f"Tank ISO code '{data.tankcode_iso}' already exists", 400)
            code.tankcode_iso = data.tankcode_iso
            
        if data.status is not None:
            code.status = data.status

        emp_id = str(getattr(current_user, "emp_id", ""))
        code.modified_by = emp_id
        
        db.commit()
        db.refresh(code)
        
        return success_resp("Tank ISO code updated successfully", code)
    except Exception as e:
        db.rollback()
        return error_resp(f"Error updating tank ISO code: {str(e)}", 500)
