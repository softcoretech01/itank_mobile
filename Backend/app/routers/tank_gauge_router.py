from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
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
    gauges = db.query(InspectionGauge).filter(InspectionGauge.tank_id == tank_id).all()
    # Map DB 'features' to JSON 'feature'
    return {
        "tank_id": tank_id,
        "gauges": [
            {
                "id": v.id,
                "feature": v.features,
                "status_id": v.status_id,
            }
            for v in gauges
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
        new_gauge = InspectionGauge(
            tank_id=data.tank_id,
            features=item.feature, # Map JSON 'feature' to DB 'features'
            status_id=item.status_id,
            status=status_str,
            created_by=user_id,
            modified_by=user_id
        )
        db.add(new_gauge)
        db.flush()
        
        resp_item = item.dict()
        resp_item['id'] = new_gauge.id
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
    existing = db.query(InspectionGauge).filter(InspectionGauge.tank_id == data.tank_id).all()
    existing_id_map = {v.id: v for v in existing if v.id is not None}
    existing_name_map = {v.features: v for v in existing}
    
    response_gauges = []
    
    for item in data.gauges:
        status_str = STATUS_MAP.get(item.status_id, "UNKNOWN")
        record = None

        if item.id and item.id in existing_id_map:
            record = existing_id_map[item.id]
        elif item.feature in existing_name_map:
            record = existing_name_map[item.feature]
        
        if record:
            record.features = item.feature
            record.status_id = item.status_id
            record.status = status_str
            record.modified_by = user_id
        else:
            record = InspectionGauge(
                tank_id=data.tank_id,
                features=item.feature,
                status_id=item.status_id,
                status=status_str,
                created_by=user_id,
                modified_by=user_id
            )
            db.add(record)
            
        db.flush()
        resp_item = item.dict()
        resp_item['id'] = record.id
        resp_item['status'] = status_str
        response_gauges.append(resp_item)

    db.commit()
    
    return {
        "tank_id": data.tank_id,
        "gauges": response_gauges
    }
