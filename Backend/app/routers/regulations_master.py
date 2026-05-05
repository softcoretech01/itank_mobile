from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import traceback

from app.database import get_db
# Import ONLY the auth helper to avoid circularity with response helpers
from app.routers.tank_inspection_router import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class RegulationCreate(BaseModel):
    regulation_name: str

class RegulationUpdate(BaseModel):
    regulation_name: Optional[str] = None
    status: Optional[int] = None

# Mock/local helpers to avoid circular imports if any
def local_success(message: str, data: Any = None, status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": jsonable_encoder(data) if data is not None else {}}
    )

def local_error(message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": {}}
    )

@router.get("/")
def get_all_regulations(db: Session = Depends(get_db)):
    try:
        results = db.execute(text("CALL sp_GetAllRegulations()")).mappings().fetchall()
        data = [dict(r) for r in results]
        return local_success("All regulations fetched", data)
    except Exception as e:
        logger.error(f"Error in get_all_regulations: {e}")
        logger.error(traceback.format_exc())
        return local_error(f"Error fetching regulations: {str(e)}", 500)

@router.get("/{id}")
def get_regulation_by_id(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("CALL sp_GetRegulationById(:id)"), {"id": id}).mappings().first()
        if not result:
            return local_error("Regulation not found", 404)
        return local_success("Regulation fetched successfully", dict(result))
    except Exception as e:
        return local_error(f"Error fetching regulation: {str(e)}", 500)

@router.post("/")
def create_regulation(
    data: RegulationCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        emp_id = None
        if hasattr(current_user, "emp_id"):
            emp_id = int(current_user.emp_id)

        result = db.execute(
            text("CALL sp_CreateRegulation(:name, :emp_id)"), 
            {"name": data.regulation_name, "emp_id": emp_id}
        ).mappings().first()
        
        db.commit()
        return local_success("Regulation created successfully", dict(result) if result else {}, 201)
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        if "already exists" in error_msg:
            return local_error(error_msg, 400)
        return local_error(f"Error creating regulation: {error_msg}", 500)

@router.put("/{id}")
def update_regulation(
    id: int, 
    data: RegulationUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        emp_id = None
        if hasattr(current_user, "emp_id"):
            emp_id = int(current_user.emp_id)
        
        result = db.execute(
            text("CALL sp_UpdateRegulation(:id, :name, :status, :emp_id)"),
            {
                "id": id,
                "name": data.regulation_name,
                "status": data.status,
                "emp_id": emp_id
            }
        ).mappings().first()

        if not result:
             return local_error("Regulation not found", 404)

        db.commit()
        return local_success("Regulation updated successfully", dict(result))
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        if "already exists" in error_msg:
            return local_error(error_msg, 400)
        return local_error(f"Error updating regulation: {error_msg}", 500)
