from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
# Ensure this matches your actual model filename
from app.models.tank_drawings import TankDrawing
from app.models.tank_header import Tank
import os
from typing import Optional
import logging
from typing import Optional
import jwt
try:
    from app.models.users_model import User
except Exception:
    User = None
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Import shared utility functions
from app.utils.upload_utils import save_uploaded_file, delete_file_if_exists
from app.utils.s3_utils import to_cdn_url

router = APIRouter()
logger = logging.getLogger(__name__)

# Get upload root from environment or default
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
## S3 migration: UPLOAD_ROOT is unused for new uploads, kept for compatibility

# Fixed Image Type for this router
DRAWING_TYPE = "drawings"

def get_emp_id_from_token(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> int:
    """
    Extract emp_id from Authorization: Bearer <token> header.
    Uses the same logic as get_current_user in tank_inspection_router.
    """

    # --- Parse header ---
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    auth = authorization.strip()
    token = auth
    if len(auth) >= 6 and auth[:6].lower() == "bearer":
        token_part = auth[6:]
        token = token_part.lstrip(" :\t")
    token = token.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    # --- Decode JWT ---
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # If no User model, read emp_id directly from payload
    if User is None:
        emp_id = payload.get("emp_id")
        if not emp_id:
            raise HTTPException(status_code=401, detail="emp_id missing in token")
        try:
            return int(emp_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid emp_id in token")

    # --- With User model: replicate get_current_user logic ---
    user_obj = None
    try:
        if "emp_id" in payload and payload["emp_id"] is not None:
            try:
                user_obj = db.query(User).filter(User.emp_id == int(payload["emp_id"])).first()
            except Exception:
                user_obj = db.query(User).filter(User.emp_id == payload["emp_id"]).first()
        elif "email" in payload and payload["email"]:
            user_obj = db.query(User).filter(User.email == payload["email"]).first()
        elif "sub" in payload and payload["sub"]:
            sub = payload["sub"]
            try:
                user_obj = db.query(User).filter((User.email == sub) | (User.emp_id == int(sub))).first()
            except Exception:
                user_obj = db.query(User).filter((User.email == sub) | (User.emp_id == sub)).first()
    except Exception:
        user_obj = None

    # Prefer emp_id from DB user record
    if user_obj is not None and getattr(user_obj, "emp_id", None) is not None:
        try:
            return int(user_obj.emp_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid emp_id in user record")

    # Fallback: emp_id from payload
    emp_id = payload.get("emp_id")
    if not emp_id:
        raise HTTPException(status_code=401, detail="emp_id missing in token/user")
    try:
        return int(emp_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid emp_id in token")

# --- CREATE (Upload) ---
@router.post("/")
@router.post("/{path_tank_id}")
def upload_drawing(
    path_tank_id: Optional[int] = None,
    tank_id: Optional[int] = Form(None),
    pid_reference: Optional[str] = Form(None),
    ga_drawing: Optional[str] = Form(None),
    pid_upload_file: Optional[UploadFile] = File(None),
    ga_upload_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    # Support tank_id from either Form or Path
    if path_tank_id is not None:
        tank_id = path_tank_id

    if tank_id is None:
         raise HTTPException(status_code=400, detail="tank_id is required")

    # Get emp_id of logged-in user from token (optional)
    emp_id = "System"
    if authorization:
        try:
            emp_id = get_emp_id_from_token(authorization)
        except Exception:
            pass
    # 1. Fetch Tank to get tank_number for folder structure
    tank_record = db.query(Tank).filter(Tank.id == tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    tank_number = tank_record.tank_number

    # 2. Save any provided files using utility
    pid_path = None
    ga_path = None
    try:
        if pid_upload_file:
            pid_path = save_uploaded_file(
                upload_file=pid_upload_file,
                tank_number=tank_number,
                image_type='pid_drawings',
                upload_root=UPLOAD_ROOT
            )
        if ga_upload_file:
            ga_path = save_uploaded_file(
                upload_file=ga_upload_file,
                tank_number=tank_number,
                image_type='ga_drawings',
                upload_root=UPLOAD_ROOT
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # 3. Check if drawing already exists for this tank, update if so, else create
    existing_drawing = db.query(TankDrawing).filter(TankDrawing.tank_id == tank_id).first()
    if existing_drawing:
        # Update existing
        if pid_reference is not None:
            existing_drawing.pid_reference = pid_reference.strip() if pid_reference and pid_reference.strip() else None
        if ga_drawing is not None:
            existing_drawing.ga_drawing = ga_drawing.strip() if ga_drawing and ga_drawing.strip() else None
        if pid_path:
            # Delete old pid file if exists
            if existing_drawing.pid_image_path:
                delete_file_if_exists(UPLOAD_ROOT, existing_drawing.pid_image_path)
            existing_drawing.pid_image_path = pid_path
            existing_drawing.pid_original_filename = pid_upload_file.filename if pid_upload_file else None
        if ga_path:
            # Delete old ga file if exists
            if existing_drawing.ga_image_path:
                delete_file_if_exists(UPLOAD_ROOT, existing_drawing.ga_image_path)
            existing_drawing.ga_image_path = ga_path
            existing_drawing.ga_original_filename = ga_upload_file.filename if ga_upload_file else None
        existing_drawing.updated_by = emp_id
        db.commit()
        db.refresh(existing_drawing)
        db_drawing = existing_drawing
    else:
        # Create new
        try:
            db_drawing = TankDrawing(
                tank_id=tank_id,
                pid_reference=pid_reference.strip() if pid_reference and pid_reference.strip() else None,
                ga_drawing=ga_drawing.strip() if ga_drawing and ga_drawing.strip() else None,
                pid_image_path=pid_path,
                ga_image_path=ga_path,
                pid_original_filename=pid_upload_file.filename if pid_upload_file else None,
                ga_original_filename=ga_upload_file.filename if ga_upload_file else None,
                created_by=emp_id,
                updated_by=emp_id
            )

            db.add(db_drawing)
            db.commit()
            db.refresh(db_drawing)
        except Exception as e:
            # Cleanup files if DB fails
            if pid_path:
                delete_file_if_exists(UPLOAD_ROOT, pid_path)
            if ga_path:
                delete_file_if_exists(UPLOAD_ROOT, ga_path)
            print(f"Database Error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Drawing uploaded successfully", "data": serialize_drawing_obj(db_drawing)}

# --- HELPER: Serialize Object ---
def serialize_drawing_obj(d):
    # Convert stored S3 keys to CDN / HTTP URLs for the frontend
    def to_url(raw):
        if not raw:
            return ""
        return to_cdn_url(raw) if "://" not in raw else raw

    return {
        "id": d.id,
        "tank_id": d.tank_id,
        "pid_reference": d.pid_reference,
        "ga_drawing": d.ga_drawing,
        "pid_image_path": to_url(d.pid_image_path),
        "ga_image_path": to_url(d.ga_image_path),
        "pid_original_filename": d.pid_original_filename,
        "ga_original_filename": d.ga_original_filename,
        "created_by": d.created_by,
        "updated_by": getattr(d, 'updated_by', None),
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }

# --- READ (List by Tank) ---
@router.get("/tank/{tank_id}")
def get_drawings_by_tank(tank_id: int, db: Session = Depends(get_db)):
    drawings = (
        db.query(TankDrawing)
        .filter(TankDrawing.tank_id == tank_id)
        .order_by(TankDrawing.created_at.desc())
        .all()
    )

    return [serialize_drawing_obj(d) for d in drawings]

    db.delete(drawing)
    db.commit()
    return {"message": "Drawing deleted successfully"}

# --- UPDATE (PUT) ---
@router.put("/{drawing_id}")
def update_drawing(
    drawing_id: int,
    pid_reference: Optional[str] = Form(None),
    ga_drawing: Optional[str] = Form(None),
    pid_upload_file: Optional[UploadFile] = File(None),
    ga_upload_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    # 1. Fetch existing drawing
    drawing = db.query(TankDrawing).filter(TankDrawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    # Get emp_id (optional, for tracking updated_by)
    emp_id = "System"
    if authorization:
        try:
            emp_id = get_emp_id_from_token(authorization)
        except Exception:
            pass

    # 2. Update fields if provided
    # Note: We treat empty strings as "clear this field" or just ignore?
    # Usually in a Form update, if not provided (None), we don't change.
    # If provided as empty string, we might want to clear it.
    # Here we strictly follow: if None, do not change.
    
    if pid_reference is not None:
        drawing.pid_reference = pid_reference.strip() if pid_reference.strip() else None
    
    if ga_drawing is not None:
        drawing.ga_drawing = ga_drawing.strip() if ga_drawing.strip() else None

    # 3. Handle File Updates
    # We need tank_number for file path
    tank_record = db.query(Tank).filter(Tank.id == drawing.tank_id).first()
    tank_number = tank_record.tank_number if tank_record else "UNKNOWN"

    try:
        if pid_upload_file:
            # Delete old file
            if drawing.pid_image_path:
                delete_file_if_exists(UPLOAD_ROOT, drawing.pid_image_path)
            # Save new
            drawing.pid_image_path = save_uploaded_file(
                upload_file=pid_upload_file,
                tank_number=tank_number,
                image_type='pid_drawings',
                upload_root=UPLOAD_ROOT
            )
            drawing.pid_original_filename = pid_upload_file.filename

        if ga_upload_file:
            # Delete old file
            if drawing.ga_image_path:
                delete_file_if_exists(UPLOAD_ROOT, drawing.ga_image_path)
            # Save new
            drawing.ga_image_path = save_uploaded_file(
                upload_file=ga_upload_file,
                tank_number=tank_number,
                image_type='ga_drawings',
                upload_root=UPLOAD_ROOT
            )
            drawing.ga_original_filename = ga_upload_file.filename

    except Exception as e:
         raise HTTPException(status_code=500, detail=f"File update failed: {str(e)}")

    drawing.updated_by = emp_id
    db.commit()
    db.refresh(drawing)

    return {"message": "Drawing updated successfully", "data": serialize_drawing_obj(drawing)}
