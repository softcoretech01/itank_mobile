from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.inspection_gauge_model import InspectionGauge
from typing import List, Optional
from pydantic import BaseModel
import jwt
import os

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# --- Helper: Get User ID from Token ---
def get_user_id(authorization: Optional[str] = Header(None)):
    if not authorization:
        return "Unknown"
    
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return str(payload.get("emp_id") or payload.get("sub") or "Unknown")
    except Exception:
        return "Unknown"

GAUGE_FEATURES_LIST = [
    "Pressure Gauge", "Tank Number", "Top",
    "Liquid Gauge", "Co. Logo", "Bottom",
    "Temp Gauge", "TEIP", "Front",
    "Gas Phase Valve", "Haz Ship Label", "Rear",
    "Liquid Phase Valve", "Handling Label", "Left",
    "Equalizing Valve", "Weight Label", "Right",
    "Pump - Smith", "T-75 / 22K7 Label", "Cross Member",
    "Motor", "Tank P&ID Plate", "Cab Door - Rear",
    "Electrical Panel", "Tank Data Plate", "Cab Door Lock",
    "Electrical Plug", "Tank CSC Plate", "Paint Condition",
    "Pump / Motor Mounting", "Std Identification Label", "Reflective Marking"
]

class GaugeItem(BaseModel):
    id: Optional[int] = None
    feature: str
    status_id: int

class GaugeRequest(BaseModel):
    tank_id: int
    gauges: List[GaugeItem]

STATUS_MAP = {
    1: "OK",
    2: "FAULTY",
    3: "NA"
}

# 1) GET /tank/{tank_id}
@router.get("/tank/{tank_id}")
def get_gauges(tank_id: int, db: Session = Depends(get_db)):
    results = db.execute(text("CALL sp_GetInspectionGaugesByTank(:tank_id)"), {"tank_id": tank_id}).mappings().fetchall()
    return {
        "tank_id": tank_id,
        "gauges": [
            {
                "id": v["id"],
                "feature": v["features"],
                "status_id": v["status_id"],
            }
            for v in results
        ]
    }

# 2) POST /create
@router.post("/create")
def create_gauges(
    data: GaugeRequest, 
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id(authorization)
    response_gauges = []
    
    for item in data.gauges:
        status_str = STATUS_MAP.get(item.status_id, "UNKNOWN")
        result = db.execute(
            text("CALL sp_UpsertInspectionGauge(:id, :tank_id, :feature, :status_id, :status, :eid)"),
            {
                "id": None,
                "tank_id": data.tank_id,
                "feature": item.feature,
                "status_id": item.status_id,
                "status": status_str,
                "eid": user_id
            }
        ).mappings().first()
        
        resp_item = item.dict()
        resp_item['id'] = result['id']
        resp_item['status'] = status_str
        response_gauges.append(resp_item)
    
    db.commit()
    
    return {
        "tank_id": data.tank_id,
        "gauges": response_gauges
    }

# 3) POST /update
@router.post("/update")
def update_gauges(
    data: GaugeRequest, 
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id(authorization)
    existing_results = db.execute(text("CALL sp_GetInspectionGaugesByTank(:tank_id)"), {"tank_id": data.tank_id}).mappings().fetchall()
    
    existing_id_map = {v["id"]: v for v in existing_results if v["id"] is not None}
    existing_name_map = {v["features"]: v for v in existing_results}
    
    response_gauges = []
    
    for item in data.gauges:
        status_str = STATUS_MAP.get(item.status_id, "UNKNOWN")
        record_id = None

        if item.id and item.id in existing_id_map:
            record_id = item.id
        elif item.feature in existing_name_map:
            record_id = existing_name_map[item.feature]["id"]

        result = db.execute(
            text("CALL sp_UpsertInspectionGauge(:id, :tank_id, :feature, :status_id, :status, :eid)"),
            {
                "id": record_id,
                "tank_id": data.tank_id,
                "feature": item.feature,
                "status_id": item.status_id,
                "status": status_str,
                "eid": user_id
            }
        ).mappings().first()
            
        resp_item = item.dict()
        resp_item['id'] = result['id']
        resp_item['status'] = status_str
        response_gauges.append(resp_item)

    db.commit()
    
    return {
        "tank_id": data.tank_id,
        "gauges": response_gauges
    }
