from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.regulations_master import RegulationsMaster
from app.routers.tank_inspection_router import get_current_user, success_resp, error_resp

router = APIRouter()

class RegulationCreate(BaseModel):
    regulation_name: str

class RegulationUpdate(BaseModel):
    regulation_name: Optional[str] = None
    status: Optional[int] = None

@router.get("/")
def get_all_regulations(db: Session = Depends(get_db)):
    try:
        results = db.query(RegulationsMaster).order_by(RegulationsMaster.id.desc()).all()
        return success_resp("All regulations fetched", results)
    except Exception as e:
        return error_resp(f"Error fetching regulations: {str(e)}", 500)

@router.get("/{id}")
def get_regulation_by_id(id: int, db: Session = Depends(get_db)):
    try:
        result = db.query(RegulationsMaster).filter(RegulationsMaster.id == id).first()
        if not result:
            return error_resp("Regulation not found", 404)
        return success_resp("Regulation fetched successfully", result)
    except Exception as e:
        return error_resp(f"Error fetching regulation: {str(e)}", 500)

@router.post("/")
def create_regulation(
    data: RegulationCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # Check if exists
        existing = db.query(RegulationsMaster).filter(RegulationsMaster.regulation_name == data.regulation_name).first()
        if existing:
            return error_resp(f"Regulation '{data.regulation_name}' already exists", 400)

        # Resolve emp_id from current_user
        emp_id = None
        if hasattr(current_user, "emp_id"):
            emp_id = int(current_user.emp_id)

        new_reg = RegulationsMaster(
            regulation_name=data.regulation_name,
            status=1,
            created_by=emp_id,
            updated_by=emp_id
        )
        db.add(new_reg)
        db.commit()
        db.refresh(new_reg)
        return success_resp("Regulation created successfully", new_reg, 201)
    except Exception as e:
        db.rollback()
        return error_resp(f"Error creating regulation: {str(e)}", 500)

@router.put("/{id}")
def update_regulation(
    id: int, 
    data: RegulationUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        reg = db.query(RegulationsMaster).filter(RegulationsMaster.id == id).first()
        if not reg:
            return error_resp("Regulation not found", 404)

        if data.regulation_name is not None:
            # Check unique
            if data.regulation_name != reg.regulation_name:
                existing = db.query(RegulationsMaster).filter(RegulationsMaster.regulation_name == data.regulation_name).first()
                if existing:
                    return error_resp(f"Regulation '{data.regulation_name}' already exists", 400)
            reg.regulation_name = data.regulation_name

        if data.status is not None:
            reg.status = data.status

        # Resolve emp_id from current_user
        emp_id = None
        if hasattr(current_user, "emp_id"):
            emp_id = int(current_user.emp_id)
        
        reg.updated_by = emp_id

        db.commit()
        db.refresh(reg)
        return success_resp("Regulation updated successfully", reg)
    except Exception as e:
        db.rollback()
        return error_resp(f"Error updating regulation: {str(e)}", 500)