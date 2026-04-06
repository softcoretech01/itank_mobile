from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tank_drawings import TankDrawing
from app.models.tank_header import Tank
import os
from typing import Optional
import logging
import jwt
try:
    from app.models.users_model import User
except Exception:
    User = None
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

from app.utils.upload_utils import save_uploaded_file, delete_file_if_exists
from app.utils.s3_utils import to_cdn_url

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
DRAWING_TYPE = "drawings"

# Max file size: 2 MB
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg"}

def validate_jpeg(upload_file: UploadFile, field_label: str):
    """Validate that file is JPEG and ≤ 2 MB."""
    content_type = getattr(upload_file, "content_type", "") or ""
    if content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_label}: Only JPEG/JPG images are allowed (got '{content_type}')."
        )
    # Read content to check size
    contents = upload_file.file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_label}: File size exceeds 2 MB limit ({len(contents) // 1024} KB uploaded)."
        )
    # Reset file pointer so save_uploaded_file can read it again
    upload_file.file.seek(0)


def get_emp_id_from_token(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> int:
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

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if User is None:
        emp_id = payload.get("emp_id")
        if not emp_id:
            raise HTTPException(status_code=401, detail="emp_id missing in token")
        try:
            return int(emp_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid emp_id in token")

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

    if user_obj is not None and getattr(user_obj, "emp_id", None) is not None:
        try:
            return int(user_obj.emp_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid emp_id in user record")

    emp_id = payload.get("emp_id")
    if not emp_id:
        raise HTTPException(status_code=401, detail="emp_id missing in token/user")
    try:
        return int(emp_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid emp_id in token")


# --- HELPER: Serialize Object ---
def serialize_drawing_obj(d):
    def to_url(raw):
        if not raw:
            return ""
        return to_cdn_url(raw) if "://" not in raw else raw

    return {
        "id": d.id,
        "tank_id": d.tank_id,
        "tank_number": getattr(d.tank, 'tank_number', None) if hasattr(d, 'tank') else None,
        "pid_reference": d.pid_reference,
        "ga_drawing": d.ga_drawing,
        "pid_drawing": to_url(getattr(d, "pid_drawing", None)),
        "pid_drawing_name": getattr(d, "pid_drawing_name", None),
        "ga_drawing_file": to_url(getattr(d, "ga_drawing_file", None)),
        "ga_drawing_file_name": getattr(d, "ga_drawing_file_name", None),
        "status": getattr(d, 'status', 1),
        "created_by": d.created_by,
        "updated_by": getattr(d, 'updated_by', None),
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


from sqlalchemy.orm import joinedload

# --- CREATE (Upload) ---
@router.post("/")
@router.post("/{path_tank_id}")
def upload_drawing(
    path_tank_id: Optional[int] = None,
    tank_id: Optional[int] = Form(None),
    pid_reference: Optional[str] = Form(None),
    ga_drawing: Optional[str] = Form(None),
    pid_drawing_file: Optional[UploadFile] = File(None),
    ga_drawing_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    if path_tank_id is not None:
        tank_id = path_tank_id

    if tank_id is None:
        raise HTTPException(status_code=400, detail="tank_id is required")

    emp_id = "System"
    if authorization:
        try:
            emp_id = get_emp_id_from_token(authorization)
        except Exception:
            pass

    tank_record = db.query(Tank).filter(Tank.id == tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Tank not found")

    tank_number = tank_record.tank_number

    # Validate & save uploaded files
    img_data = {}
    try:
        if pid_drawing_file and pid_drawing_file.filename:
            validate_jpeg(pid_drawing_file, "P&ID Drawing")
            path = save_uploaded_file(
                upload_file=pid_drawing_file,
                tank_number=tank_number,
                image_type='drawing_pid',
                upload_root=UPLOAD_ROOT
            )
            img_data["pid_drawing"] = path
            img_data["pid_drawing_name"] = pid_drawing_file.filename
        else:
            img_data["pid_drawing"] = None
            img_data["pid_drawing_name"] = None

        if ga_drawing_file and ga_drawing_file.filename:
            validate_jpeg(ga_drawing_file, "GA Drawing")
            path = save_uploaded_file(
                upload_file=ga_drawing_file,
                tank_number=tank_number,
                image_type='drawing_ga',
                upload_root=UPLOAD_ROOT
            )
            img_data["ga_drawing_file"] = path
            img_data["ga_drawing_file_name"] = ga_drawing_file.filename
        else:
            img_data["ga_drawing_file"] = None
            img_data["ga_drawing_file_name"] = None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    existing_drawing = db.query(TankDrawing).filter(TankDrawing.tank_id == tank_id).first()
    if existing_drawing:
        if pid_reference is not None:
            existing_drawing.pid_reference = pid_reference.strip() if pid_reference and pid_reference.strip() else None
        if ga_drawing is not None:
            existing_drawing.ga_drawing = ga_drawing.strip() if ga_drawing and ga_drawing.strip() else None

        if img_data.get("pid_drawing"):
            old = existing_drawing.pid_drawing
            if old:
                delete_file_if_exists(UPLOAD_ROOT, old)
            existing_drawing.pid_drawing = img_data["pid_drawing"]
            existing_drawing.pid_drawing_name = img_data["pid_drawing_name"]

        if img_data.get("ga_drawing_file"):
            old = existing_drawing.ga_drawing_file
            if old:
                delete_file_if_exists(UPLOAD_ROOT, old)
            existing_drawing.ga_drawing_file = img_data["ga_drawing_file"]
            existing_drawing.ga_drawing_file_name = img_data["ga_drawing_file_name"]

        existing_drawing.updated_by = emp_id
        db.commit()
        db.refresh(existing_drawing)
        db_drawing = existing_drawing
    else:
        try:
            db_drawing = TankDrawing(
                tank_id=tank_id,
                pid_reference=pid_reference.strip() if pid_reference and pid_reference.strip() else None,
                ga_drawing=ga_drawing.strip() if ga_drawing and ga_drawing.strip() else None,
                pid_drawing=img_data.get("pid_drawing"),
                pid_drawing_name=img_data.get("pid_drawing_name"),
                ga_drawing_file=img_data.get("ga_drawing_file"),
                ga_drawing_file_name=img_data.get("ga_drawing_file_name"),
                created_by=emp_id,
                updated_by=emp_id
            )
            db.add(db_drawing)
            db.commit()
            db.refresh(db_drawing)
        except Exception as e:
            for key in ["pid_drawing", "ga_drawing_file"]:
                p = img_data.get(key)
                if p:
                    delete_file_if_exists(UPLOAD_ROOT, p)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Drawing uploaded successfully", "data": serialize_drawing_obj(db_drawing)}


# --- READ (List All) ---
@router.get("/")
def get_all_drawings(db: Session = Depends(get_db)):
    drawings = db.query(TankDrawing).options(joinedload(TankDrawing.tank)).all()
    return [serialize_drawing_obj(d) for d in drawings]


# --- READ (List by Tank) ---
@router.get("/tank/{tank_id}")
def get_drawings_by_tank(tank_id: int, db: Session = Depends(get_db)):
    drawings = (
        db.query(TankDrawing)
        .options(joinedload(TankDrawing.tank))
        .filter(TankDrawing.tank_id == tank_id)
        .order_by(TankDrawing.created_at.desc())
        .all()
    )
    return [serialize_drawing_obj(d) for d in drawings]


# --- DELETE ---
@router.delete("/{drawing_id}")
def delete_drawing(drawing_id: int, db: Session = Depends(get_db)):
    drawing = db.query(TankDrawing).filter(TankDrawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    for field in ["pid_drawing", "ga_drawing_file"]:
        p = getattr(drawing, field, None)
        if p:
            delete_file_if_exists(UPLOAD_ROOT, p)

    db.delete(drawing)
    db.commit()
    return {"message": "Drawing deleted successfully"}


# --- UPDATE (PUT) ---
@router.put("/{drawing_id}")
def update_drawing(
    drawing_id: int,
    pid_reference: Optional[str] = Form(None),
    ga_drawing: Optional[str] = Form(None),
    status: Optional[int] = Form(None),
    pid_drawing_file: Optional[UploadFile] = File(None),
    ga_drawing_file: Optional[UploadFile] = File(None),
    clear_pid_drawing: Optional[str] = Form(None),
    clear_ga_drawing_file: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    drawing = db.query(TankDrawing).filter(TankDrawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    emp_id = "System"
    if authorization:
        try:
            emp_id = get_emp_id_from_token(authorization)
        except Exception:
            pass

    if pid_reference is not None:
        drawing.pid_reference = pid_reference.strip() if pid_reference.strip() else None

    if ga_drawing is not None:
        drawing.ga_drawing = ga_drawing.strip() if ga_drawing.strip() else None

    if status is not None:
        drawing.status = 1 if int(status) == 1 else 0

    tank_record = db.query(Tank).filter(Tank.id == drawing.tank_id).first()
    tank_number = tank_record.tank_number if tank_record else "UNKNOWN"

    try:
        # --- Handle clear requests ---
        if clear_pid_drawing == '1':
            if drawing.pid_drawing:
                delete_file_if_exists(UPLOAD_ROOT, drawing.pid_drawing)
            drawing.pid_drawing = None
            drawing.pid_drawing_name = None

        if clear_ga_drawing_file == '1':
            if drawing.ga_drawing_file:
                delete_file_if_exists(UPLOAD_ROOT, drawing.ga_drawing_file)
            drawing.ga_drawing_file = None
            drawing.ga_drawing_file_name = None

        if pid_drawing_file and pid_drawing_file.filename:
            validate_jpeg(pid_drawing_file, "P&ID Drawing")
            old = drawing.pid_drawing
            if old:
                delete_file_if_exists(UPLOAD_ROOT, old)
            new_path = save_uploaded_file(
                upload_file=pid_drawing_file,
                tank_number=tank_number,
                image_type='drawing_pid',
                upload_root=UPLOAD_ROOT
            )
            drawing.pid_drawing = new_path
            drawing.pid_drawing_name = pid_drawing_file.filename

        if ga_drawing_file and ga_drawing_file.filename:
            validate_jpeg(ga_drawing_file, "GA Drawing")
            old = drawing.ga_drawing_file
            if old:
                delete_file_if_exists(UPLOAD_ROOT, old)
            new_path = save_uploaded_file(
                upload_file=ga_drawing_file,
                tank_number=tank_number,
                image_type='drawing_ga',
                upload_root=UPLOAD_ROOT
            )
            drawing.ga_drawing_file = new_path
            drawing.ga_drawing_file_name = ga_drawing_file.filename

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File update failed: {str(e)}")

    drawing.updated_by = emp_id
    db.commit()
    db.refresh(drawing)

    return {"message": "Drawing updated successfully", "data": serialize_drawing_obj(drawing)}
