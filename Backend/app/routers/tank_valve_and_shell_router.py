from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.tank_valve_and_shell_model import TankValveAndShell
from app.models.tank_header import Tank
from typing import Optional, List
import os
import uuid
import logging
from app.utils.upload_utils import save_uploaded_file, delete_file_if_exists
from app.utils.s3_utils import to_cdn_url

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
VALVE_TYPE = "valve_shell"

def get_emp_id_from_token(authorization: Optional[str] = Header(None)) -> str:
    """Soft-auth: extracts emp_id from JWT or returns 'System' on failure."""
    if not authorization:
        return "System"
    try:
        token = authorization.replace("Bearer ", "").strip()
        # Mocking JWT decode for now, in a real app use secret/lib
        import jwt
        JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
        JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return str(payload.get("emp_id") or "System")
    except Exception:
        return "System"

# --- HELPER: Serialize Object ---
def serialize_valve_shell_obj(record, request: Optional[Request] = None):
    def process_url(path):
        if not path:
            return None
        url = to_cdn_url(path)
        if url and not url.startswith("http") and request:
            base = f"{request.url.scheme}://{request.url.netloc}"
            url = f"{base}/{url.lstrip('/')}"
        return url

    return {
        "id": record.id,
        "tank_id": record.tank_id,
        "tank_number": getattr(record.tank, 'tank_number', None) if hasattr(record, 'tank') else None,
        "valve_label_image_path": record.valve_label_image_path,
        "valve_label_thumbnail_path": record.valve_label_thumbnail_path,
        "tank_frame_image_path": record.tank_frame_image_path,
        "tank_frame_thumbnail_path": record.tank_frame_thumbnail_path,
        "valve_label_image_url": process_url(record.valve_label_image_path),
        "valve_label_thumbnail_url": process_url(record.valve_label_thumbnail_path),
        "tank_frame_image_url": process_url(record.tank_frame_image_path),
        "tank_frame_thumbnail_url": process_url(record.tank_frame_thumbnail_path),
        "status": getattr(record, 'status', 1),
        "created_by": record.created_by,
        "modified_by": record.modified_by,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "modified_at": record.modified_at.isoformat() if record.modified_at else None,
    }

# --- READ (List All) ---
@router.get("/")
def get_all_valve_shell(db: Session = Depends(get_db), request: Request = None):
    records = db.query(TankValveAndShell).options(joinedload(TankValveAndShell.tank)).all()
    return [serialize_valve_shell_obj(r, request) for r in records]

# --- READ (Get One by ID) ---
@router.get("/{id}")
def get_one_valve_shell(id: int, request: Request, db: Session = Depends(get_db)):
    record = db.query(TankValveAndShell).options(joinedload(TankValveAndShell.tank)).filter(TankValveAndShell.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Valve/Shell record not found")
    return serialize_valve_shell_obj(record, request)

# --- READ (Get by Tank ID) ---
@router.get("/tank/{tank_id}")
def get_by_tank(tank_id: int, request: Request, db: Session = Depends(get_db)):
    record = db.query(TankValveAndShell).filter(TankValveAndShell.tank_id == tank_id).first()
    if not record:
        return {"tank_id": tank_id, "data": None}
    return {"tank_id": tank_id, "data": serialize_valve_shell_obj(record, request)}

# --- CREATE/UPDATE (Upsert) ---
@router.post("/")
@router.post("/update")
def create_valve_shell(
    tank_id: int = Form(...),
    valve_label_file: Optional[UploadFile] = File(None),
    tank_frame_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    emp_id: str = Depends(get_emp_id_from_token)
):
    tank_record = db.query(Tank).filter(Tank.id == tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Tank not found")

    # Upsert logic
    record = db.query(TankValveAndShell).filter(TankValveAndShell.tank_id == tank_id).first()
    
    # Process uploads
    if valve_label_file and valve_label_file.filename:
        v_path = save_uploaded_file(valve_label_file, tank_record.tank_number, "valve_label", UPLOAD_ROOT)
    else:
        v_path = None

    if tank_frame_file and tank_frame_file.filename:
        f_path = save_uploaded_file(tank_frame_file, tank_record.tank_number, "tank_frame", UPLOAD_ROOT)
    else:
        f_path = None

    if record:
        if v_path:
            delete_file_if_exists(UPLOAD_ROOT, record.valve_label_image_path)
            record.valve_label_image_path = v_path
        if f_path:
            delete_file_if_exists(UPLOAD_ROOT, record.tank_frame_image_path)
            record.tank_frame_image_path = f_path
        record.modified_by = emp_id
    else:
        record = TankValveAndShell(
            tank_id=tank_id,
            valve_label_image_path=v_path,
            tank_frame_image_path=f_path,
            created_by=emp_id,
            modified_by=emp_id
        )
        db.add(record)
    
    db.commit()
    db.refresh(record)
    return {"success": True, "data": serialize_valve_shell_obj(record)}

# --- UPDATE (PUT by ID) ---
@router.put("/{id}")
def update_valve_shell(
    id: int,
    status: Optional[int] = Form(None),
    valve_label_file: Optional[UploadFile] = File(None),
    tank_frame_file: Optional[UploadFile] = File(None),
    clear_valve_label: Optional[str] = Form(None),
    clear_tank_frame: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    emp_id: str = Depends(get_emp_id_from_token)
):
    record = db.query(TankValveAndShell).filter(TankValveAndShell.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    tank_rec = db.query(Tank).filter(Tank.id == record.tank_id).first()
    tank_no = tank_rec.tank_number if tank_rec else "UNKNOWN"

    # Handle status
    if status is not None:
        record.status = 1 if int(status) == 1 else 0

    # Handle clears
    if clear_valve_label == '1':
        delete_file_if_exists(UPLOAD_ROOT, record.valve_label_image_path)
        record.valve_label_image_path = None
        record.valve_label_thumbnail_path = None
    
    if clear_tank_frame == '1':
        delete_file_if_exists(UPLOAD_ROOT, record.tank_frame_image_path)
        record.tank_frame_image_path = None
        record.tank_frame_thumbnail_path = None

    # Handle replacement uploads
    if valve_label_file and valve_label_file.filename:
        delete_file_if_exists(UPLOAD_ROOT, record.valve_label_image_path)
        record.valve_label_image_path = save_uploaded_file(valve_label_file, tank_no, "valve_label", UPLOAD_ROOT)
    
    if tank_frame_file and tank_frame_file.filename:
        delete_file_if_exists(UPLOAD_ROOT, record.tank_frame_image_path)
        record.tank_frame_image_path = save_uploaded_file(tank_frame_file, tank_no, "tank_frame", UPLOAD_ROOT)

    record.modified_by = emp_id
    db.commit()
    return {"success": True, "message": "Updated successfully"}

# --- DELETE ---
@router.delete("/{id}")
def delete_valve_shell(id: int, db: Session = Depends(get_db)):
    record = db.query(TankValveAndShell).filter(TankValveAndShell.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    
    delete_file_if_exists(UPLOAD_ROOT, record.valve_label_image_path)
    delete_file_if_exists(UPLOAD_ROOT, record.tank_frame_image_path)
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "Deleted successfully"}
