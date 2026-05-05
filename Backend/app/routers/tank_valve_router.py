from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.inspection_valve_model import InspectionValve
from typing import List, Optional
from pydantic import BaseModel
import jwt
import os

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def get_user_id(authorization: Optional[str] = Header(None)):
    if not authorization:
        return "Unknown"
    
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return str(payload.get("emp_id") or payload.get("sub") or "Unknown")
    except Exception:
        return "Unknown"

# STANDARD HYPHENS ONLY
VALVE_FEATURES_LIST = [
    "Top Fill - Gas", "Emergency Valve - A3", "S/V - 1",
    "Iso - Top Fill", "Trycock - 1", "S/V - 2",
    "Bottom fill - Liq", "Trycock - 2 / 3", "S/V - 3",
    "Iso - Bottom Fill - A3", "Vacuum Valve", "S/V - 4",
    "Iso - Top / Bottom", "T-Couple Valve", "S/V - B.Disc",
    "Drain Valve", "T-Couple DV-6", "S/V Diverter",
    "Blow Valve", "Liq Connection", "Line SRV - 1",
    "PB Valve Inlet", "Gas Connection", "Line SRV - 2",
    "PB Valve Return", "Vent Pipe", "Line SRV - 3",
    "PB Unit", "Pipe / Support", "Line SRV - 4 / 5",
    "Sample Valve", "Check Valve", "Out Ves B.Disc"
]

class ValveItem(BaseModel):
    id: Optional[int] = None
    feature: str
    status_id: int

class ValveRequest(BaseModel):
    tank_id: int
    valves: List[ValveItem]

STATUS_MAP = {
    1: "OK",
    2: "FAULTY",
    3: "NA"
}

@router.get("/tank/{tank_id}")
def get_valves(tank_id: int, db: Session = Depends(get_db)):
    results = db.execute(text("CALL sp_GetInspectionValvesByTank(:tank_id)"), {"tank_id": tank_id}).mappings().fetchall()
    return {
        "tank_id": tank_id,
        "valves": [
            {
                "id": v["id"],
                "feature": v["features"],
                "status_id": v["status_id"],
            }
            for v in results
        ]
    }

@router.post("/create")
def create_valves(
    data: ValveRequest, 
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id(authorization)
    response_valves = []
    
    for item in data.valves:
        status_str = STATUS_MAP.get(item.status_id, "UNKNOWN")
        result = db.execute(
            text("CALL sp_UpsertInspectionValve(:id, :tank_id, :feature, :status_id, :status, :eid)"),
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
        response_valves.append(resp_item)
    
    db.commit()
    
    return {
        "tank_id": data.tank_id,
        "valves": response_valves
    }

@router.post("/update")
def update_valves(
    data: ValveRequest, 
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id(authorization)
    existing_results = db.execute(text("CALL sp_GetInspectionValvesByTank(:tank_id)"), {"tank_id": data.tank_id}).mappings().fetchall()
    
    existing_id_map = {v["id"]: v for v in existing_results if v["id"] is not None}
    existing_name_map = {v["features"]: v for v in existing_results}
    
    response_valves = []
    
    for item in data.valves:
        status_str = STATUS_MAP.get(item.status_id, "UNKNOWN")
        record_id = None

        if item.id and item.id in existing_id_map:
            record_id = item.id
        elif item.feature in existing_name_map:
            record_id = existing_name_map[item.feature]["id"]

        result = db.execute(
            text("CALL sp_UpsertInspectionValve(:id, :tank_id, :feature, :status_id, :status, :eid)"),
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
        response_valves.append(resp_item)

    db.commit()
    
    return {
        "tank_id": data.tank_id,
        "valves": response_valves
    }
