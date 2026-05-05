from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.tank_drawings import TankDrawing
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
    # Reset file pointer so save_uploaded_file can read it aimage2in
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

    # Support both SQLAlchemy Row objects (dot notation) and RowMapping/dict objects (bracket notation)
    def get_val(obj, key, default=None):
        if hasattr(obj, key):
            return getattr(obj, key)
        try:
            return obj[key]
        except (KeyError, TypeError):
            return default

    return {
        "id": get_val(d, "id"),
        "pid_reference": get_val(d, "pid_reference"),
        "pid_drawing": to_url(get_val(d, "pid_drawing")),
        "pid_drawing_name": get_val(d, "pid_drawing_name"),
        "image2_drawing_file": to_url(get_val(d, "image2_drawing_file")),
        "image2_drawing_file_name": get_val(d, "image2_drawing_file_name"),
        "img3": to_url(get_val(d, "img3")),
        "img3_name": get_val(d, "img3_name"),
        "img4": to_url(get_val(d, "img4")),
        "img4_name": get_val(d, "img4_name"),
        "img5": to_url(get_val(d, "img5")),
        "img5_name": get_val(d, "img5_name"),
        "img6": to_url(get_val(d, "img6")),
        "img6_name": get_val(d, "img6_name"),
        "status": 0 if get_val(d, 'status', 1) == 0 else 1,
        "remarks": get_val(d, 'remarks', "") or "",
        "created_by": get_val(d, "created_by"),
        "updated_by": get_val(d, 'updated_by'),
        "created_at": get_val(d, "created_at").isoformat() if get_val(d, "created_at") else None,
        "updated_at": get_val(d, "updated_at").isoformat() if get_val(d, "updated_at") else None,
    }


from sqlalchemy.orm import joinedload

# --- CREATE (Upload) ---
@router.post("/")
@router.post("/{path_tank_id}")
def upload_drawing(
    path_tank_id: Optional[int] = None,
    pid_reference: Optional[str] = Form(None),
    pid_drawing_file: Optional[UploadFile] = File(None),
    image2_drawing_file: Optional[UploadFile] = File(None),
    img3_file: Optional[UploadFile] = File(None),
    img4_file: Optional[UploadFile] = File(None),
    img5_file: Optional[UploadFile] = File(None),
    img6_file: Optional[UploadFile] = File(None),
    remarks: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    emp_id = "System"
    if authorization:
        try:
            emp_id = get_emp_id_from_token(authorization)
        except Exception:
            pass

    tank_number = "GLOBAL"

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

        if image2_drawing_file and image2_drawing_file.filename:
            validate_jpeg(image2_drawing_file, "image2 Drawing")
            path = save_uploaded_file(
                upload_file=image2_drawing_file,
                tank_number=tank_number,
                image_type='drawing_image2',
                upload_root=UPLOAD_ROOT
            )
            img_data["image2_drawing_file"] = path
            img_data["image2_drawing_file_name"] = image2_drawing_file.filename
        else:
            img_data["image2_drawing_file"] = None
            img_data["image2_drawing_file_name"] = None

        # Additional 4 images
        for idx in range(3, 7):
            f_key = f"img{idx}_file"
            f_obj = locals().get(f_key)
            if f_obj and f_obj.filename:
                validate_jpeg(f_obj, f"Image {idx}")
                path = save_uploaded_file(
                    upload_file=f_obj,
                    tank_number=tank_number,
                    image_type=f'drawing_img{idx}',
                    upload_root=UPLOAD_ROOT
                )
                img_data[f"img{idx}"] = path
                img_data[f"img{idx}_name"] = f_obj.filename
            else:
                img_data[f"img{idx}"] = None
                img_data[f"img{idx}_name"] = None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    if pid_reference:
        ref = pid_reference.strip()
        dup = db.execute(text("SELECT id FROM tank_drawings WHERE pid_reference = :ref LIMIT 1"), {"ref": ref}).mappings().first()
        if dup:
            raise HTTPException(status_code=400, detail="This P&ID Reference already exists.")

    try:
        result = db.execute(
            text("CALL sp_CreateDrawing(:pid_ref, :pid_draw, :pid_draw_name, :img2, :img2_name, :img3, :img3_name, :img4, :img4_name, :img5, :img5_name, :img6, :img6_name, :remarks, :eid)"),
            {
                "pid_ref": pid_reference.strip() if pid_reference and pid_reference.strip() else None,
                "pid_draw": img_data.get("pid_drawing"),
                "pid_draw_name": img_data.get("pid_drawing_name"),
                "img2": img_data.get("image2_drawing_file"),
                "img2_name": img_data.get("image2_drawing_file_name"),
                "img3": img_data.get("img3"),
                "img3_name": img_data.get("img3_name"),
                "img4": img_data.get("img4"),
                "img4_name": img_data.get("img4_name"),
                "img5": img_data.get("img5"),
                "img5_name": img_data.get("img5_name"),
                "img6": img_data.get("img6"),
                "img6_name": img_data.get("img6_name"),
                "remarks": remarks.strip() if remarks and remarks.strip() else None,
                "eid": str(emp_id)
            }
        ).mappings().first()
        db.commit()
        return {"message": "Drawing uploaded successfully", "data": serialize_drawing_obj(result) if result else {}}
    except Exception as e:
        db.rollback()
        for key in ["pid_drawing", "image2_drawing_file", "img3", "img4", "img5", "img6"]:
            p = img_data.get(key)
            if p:
                delete_file_if_exists(UPLOAD_ROOT, p)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# --- READ (List All) ---
@router.get("/")
def get_all_drawings(db: Session = Depends(get_db)):
    results = db.execute(text("CALL sp_GetAllDrawings()")).mappings().fetchall()
    return [serialize_drawing_obj(r) for r in results]


# --- READ (List by Tank) ---
@router.get("/all")
def get_drawings_list(db: Session = Depends(get_db)):
    results = db.execute(text("CALL sp_GetAllDrawings()")).mappings().fetchall()
    return [serialize_drawing_obj(r) for r in results]


# --- DELETE ---
@router.delete("/{drawing_id}")
def delete_drawing(drawing_id: int, db: Session = Depends(get_db)):
    drawing = db.execute(text("CALL sp_GetDrawingById(:id)"), {"id": drawing_id}).mappings().first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    for field in ["pid_drawing", "image2_drawing_file", "img3", "img4", "img5", "img6"]:
        p = drawing.get(field)
        if p:
            delete_file_if_exists(UPLOAD_ROOT, p)

    db.execute(text("CALL sp_DeleteDrawing(:id)"), {"id": drawing_id})
    db.commit()
    return {"message": "Drawing deleted successfully"}


# --- UPDATE (PUT) ---
@router.put("/{drawing_id}")
def update_drawing(
    drawing_id: int,
    pid_reference: Optional[str] = Form(None),
    status: Optional[int] = Form(None),
    pid_drawing_file: Optional[UploadFile] = File(None),
    image2_drawing_file: Optional[UploadFile] = File(None),
    img3_file: Optional[UploadFile] = File(None),
    img4_file: Optional[UploadFile] = File(None),
    img5_file: Optional[UploadFile] = File(None),
    img6_file: Optional[UploadFile] = File(None),
    remarks: Optional[str] = Form(None),
    clear_pid_drawing: Optional[str] = Form(None),
    clear_image2_drawing_file: Optional[str] = Form(None),
    clear_img3: Optional[str] = Form(None),
    clear_img4: Optional[str] = Form(None),
    clear_img5: Optional[str] = Form(None),
    clear_img6: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    drawing = db.execute(text("CALL sp_GetDrawingById(:id)"), {"id": drawing_id}).mappings().first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    emp_id = "System"
    if authorization:
        try:
            emp_id = get_emp_id_from_token(authorization)
        except Exception:
            pass

    # Copy current values to a dictionary for updating
    upd = dict(drawing)

    if pid_reference is not None:
        ref = pid_reference.strip()
        other = db.execute(text("SELECT id FROM tank_drawings WHERE pid_reference = :ref AND id <> :id LIMIT 1"), {"ref": ref, "id": drawing_id}).mappings().first()
        if other:
            raise HTTPException(status_code=400, detail="This P&ID Reference already exists.")
        upd["pid_reference"] = ref if ref else None

    if status is not None:
        upd["status"] = 1 if int(status) == 1 else 0

    if remarks is not None:
        upd["remarks"] = remarks.strip() if remarks and remarks.strip() else None

    tank_number = "GLOBAL"

    try:
        # --- Handle clear requests ---
        if clear_pid_drawing == '1':
            if upd["pid_drawing"]:
                delete_file_if_exists(UPLOAD_ROOT, upd["pid_drawing"])
            upd["pid_drawing"] = None
            upd["pid_drawing_name"] = None

        if clear_image2_drawing_file == '1':
            if upd["image2_drawing_file"]:
                delete_file_if_exists(UPLOAD_ROOT, upd["image2_drawing_file"])
            upd["image2_drawing_file"] = None
            upd["image2_drawing_file_name"] = None

        if pid_drawing_file and pid_drawing_file.filename:
            validate_jpeg(pid_drawing_file, "P&ID Drawing")
            old = upd["pid_drawing"]
            if old:
                delete_file_if_exists(UPLOAD_ROOT, old)
            new_path = save_uploaded_file(
                upload_file=pid_drawing_file,
                tank_number=tank_number,
                image_type='drawing_pid',
                upload_root=UPLOAD_ROOT
            )
            upd["pid_drawing"] = new_path
            upd["pid_drawing_name"] = pid_drawing_file.filename

        if image2_drawing_file and image2_drawing_file.filename:
            validate_jpeg(image2_drawing_file, "image2 Drawing")
            old = upd["image2_drawing_file"]
            if old:
                delete_file_if_exists(UPLOAD_ROOT, old)
            new_path = save_uploaded_file(
                upload_file=image2_drawing_file,
                tank_number=tank_number,
                image_type='drawing_image2',
                upload_root=UPLOAD_ROOT
            )
            upd["image2_drawing_file"] = new_path
            upd["image2_drawing_file_name"] = image2_drawing_file.filename

        # Additional 4 images
        for idx in range(3, 7):
            f_key = f"img{idx}_file"
            clear_key = f"clear_img{idx}"
            col_key = f"img{idx}"
            name_key = col_key + "_name"

            if locals().get(clear_key) == '1':
                old = upd[col_key]
                if old:
                    delete_file_if_exists(UPLOAD_ROOT, old)
                upd[col_key] = None
                upd[name_key] = None

            f_obj = locals().get(f_key)
            if f_obj and f_obj.filename:
                validate_jpeg(f_obj, f"Image {idx}")
                old = upd[col_key]
                if old:
                    delete_file_if_exists(UPLOAD_ROOT, old)
                new_path = save_uploaded_file(
                    upload_file=f_obj,
                    tank_number=tank_number,
                    image_type=f'drawing_img{idx}',
                    upload_root=UPLOAD_ROOT
                )
                upd[col_key] = new_path
                upd[name_key] = f_obj.filename

        # Finally, call the update procedure
        result = db.execute(
            text("CALL sp_UpdateDrawing(:id, :pid_ref, :status, :pid_draw, :pid_draw_name, :img2, :img2_name, :img3, :img3_name, :img4, :img4_name, :img5, :img5_name, :img6, :img6_name, :remarks, :eid)"),
            {
                "id": drawing_id,
                "pid_ref": upd["pid_reference"],
                "status": upd["status"],
                "pid_draw": upd["pid_drawing"],
                "pid_draw_name": upd["pid_drawing_name"],
                "img2": upd["image2_drawing_file"],
                "img2_name": upd["image2_drawing_file_name"],
                "img3": upd["img3"],
                "img3_name": upd["img3_name"],
                "img4": upd["img4"],
                "img4_name": upd["img4_name"],
                "img5": upd["img5"],
                "img5_name": upd["img5_name"],
                "img6": upd["img6"],
                "img6_name": upd["img6_name"],
                "remarks": upd["remarks"],
                "eid": str(emp_id)
            }
        ).mappings().first()
        db.commit()
        return {"message": "Drawing updated successfully", "data": dict(result) if result else {}}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"File update failed: {str(e)}")
