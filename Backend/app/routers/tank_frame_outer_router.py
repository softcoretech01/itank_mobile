from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from sqlalchemy import text
from app.models.tank_frame_outer_model import TankFrameOuter
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
VALVE_TYPE = "ga"

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
def serialize_ga_obj(record, request: Optional[Request] = None):
    def process_url(path):
        if not path:
            return None
        url = to_cdn_url(path)
        if url and not url.startswith("http") and request:
            base = f"{request.url.scheme}://{request.url.netloc}"
            url = f"{base}/{url.lstrip('/')}"
        return url

    # Support both SQLAlchemy Row objects (dot notation) and RowMapping/dict objects (bracket notation)
    def get_val(obj, key, default=None):
        if hasattr(obj, key):
            return getattr(obj, key)
        try:
            return obj[key]
        except (KeyError, TypeError):
            return default

    return {
        "id": get_val(record, "id"),
        "ga_reference": get_val(record, "ga_reference"),
        "ga_image_path": get_val(record, "ga_image_path"),
        "ga_thumbnail_path": get_val(record, "ga_thumbnail_path"),
        "image2_image_path": get_val(record, "image2_image_path"),
        "image2_thumbnail_path": get_val(record, "image2_thumbnail_path"),
        "valve_label_image_path": get_val(record, "ga_image_path"),
        "valve_label_thumbnail_path": get_val(record, "ga_thumbnail_path"),
        "tank_frame_image_path": get_val(record, "image2_image_path"),
        "tank_frame_thumbnail_path": get_val(record, "image2_thumbnail_path"),
        "ga_image_url": process_url(get_val(record, "ga_image_path")),
        "ga_thumbnail_url": process_url(get_val(record, "ga_thumbnail_path")),
        "image2_image_url": process_url(get_val(record, "image2_image_path")),
        "image2_thumbnail_url": process_url(get_val(record, "image2_thumbnail_path")),
        "valve_label_image_url": process_url(get_val(record, "ga_image_path")),
        "valve_label_thumbnail_url": process_url(get_val(record, "ga_thumbnail_path")),
        "tank_frame_image_url": process_url(get_val(record, "image2_image_path")),
        "tank_frame_thumbnail_url": process_url(get_val(record, "image2_thumbnail_path")),
        "img3_path": get_val(record, "img3_path"),
        "img4_path": get_val(record, "img4_path"),
        "img5_path": get_val(record, "img5_path"),
        "img6_path": get_val(record, "img6_path"),
        "img3_url": process_url(get_val(record, "img3_path")),
        "img4_url": process_url(get_val(record, "img4_path")),
        "img5_url": process_url(get_val(record, "img5_path")),
        "img6_url": process_url(get_val(record, "img6_path")),
        "status": 0 if get_val(record, 'status', 1) == 0 else 1,
        "remarks": get_val(record, 'remarks', "") or "",
        "created_by": get_val(record, "created_by"),
        "modified_by": get_val(record, "modified_by"),
        "created_at": get_val(record, "created_at").isoformat() if get_val(record, "created_at") else None,
        "modified_at": get_val(record, "modified_at").isoformat() if get_val(record, "modified_at") else None,
    }

# --- READ (List All) ---
@router.get("/")
def get_all_ga(db: Session = Depends(get_db), request: Request = None):
    results = db.execute(text("CALL sp_GetAllFrameOuters()")).mappings().fetchall()
    return [serialize_ga_obj(r, request) for r in results]

# --- READ (Get One by ID) ---
@router.get("/{id}")
def get_one_ga(id: int, request: Request, db: Session = Depends(get_db)):
    record = db.execute(text("CALL sp_GetFrameOuterById(:id)"), {"id": id}).mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Valve/Shell record not found")
    return serialize_ga_obj(record, request)

# --- READ (Get by Tank ID) ---
@router.get("/get/all")
def get_ga_all_list(request: Request, db: Session = Depends(get_db)):
    results = db.execute(text("CALL sp_GetAllFrameOuters()")).mappings().fetchall()
    return [serialize_ga_obj(r, request) for r in results]

# --- CREATE/UPDATE (Upsert) ---
@router.post("/")
@router.post("/update")
def create_ga(
    ga_image_path: Optional[UploadFile] = File(None),
    image2_image_path: Optional[UploadFile] = File(None),
    ga_file: Optional[UploadFile] = File(None),
    image2_file: Optional[UploadFile] = File(None),
    valve_label_file: Optional[UploadFile] = File(None),
    tank_frame_file: Optional[UploadFile] = File(None),
    img3_file: Optional[UploadFile] = File(None),
    img4_file: Optional[UploadFile] = File(None),
    img5_file: Optional[UploadFile] = File(None),
    img6_file: Optional[UploadFile] = File(None),
    remarks: Optional[str] = Form(None),
    ga_reference: Optional[str] = Form(None),
    record_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    emp_id: str = Depends(get_emp_id_from_token)
):
    tank_no = "GLOBAL"
    
    # Upsert logic based on record_id
    record = None
    if record_id:
        record = db.execute(text("CALL sp_GetFrameOuterById(:id)"), {"id": record_id}).mappings().first()
    
    if ga_reference:
        ref = ga_reference.strip()
        query_str = "SELECT id FROM tank_frame_outer WHERE ga_reference = :ref"
        params = {"ref": ref}
        if record:
            query_str += " AND id <> :id"
            params["id"] = record["id"]
        
        dup = db.execute(text(query_str), params).mappings().first()
        if dup:
            raise HTTPException(status_code=400, detail="This GA Reference already exists.")
    
    # Process uploads
    if ga_image_path and ga_image_path.filename:
        v_path = save_uploaded_file(ga_image_path, tank_no, "valve_label", UPLOAD_ROOT)
    elif valve_label_file and valve_label_file.filename:
        v_path = save_uploaded_file(valve_label_file, tank_no, "valve_label", UPLOAD_ROOT)
    elif ga_file and ga_file.filename:
        v_path = save_uploaded_file(ga_file, tank_no, "valve_label", UPLOAD_ROOT)
    else:
        v_path = record["ga_image_path"] if record else None

    if image2_image_path and image2_image_path.filename:
        f_path = save_uploaded_file(image2_image_path, tank_no, "tank_frame", UPLOAD_ROOT)
    elif tank_frame_file and tank_frame_file.filename:
        f_path = save_uploaded_file(tank_frame_file, tank_no, "tank_frame", UPLOAD_ROOT)
    elif image2_file and image2_file.filename:
        f_path = save_uploaded_file(image2_file, tank_no, "tank_frame", UPLOAD_ROOT)
    else:
        f_path = record["image2_image_path"] if record else None

    paths = {}
    for idx in range(3, 7):
        f_obj = locals().get(f"img{idx}_file")
        if f_obj and f_obj.filename:
            paths[f"img{idx}_path"] = save_uploaded_file(f_obj, tank_no, f"valve_img{idx}", UPLOAD_ROOT)
        else:
            paths[f"img{idx}_path"] = record[f"img{idx}_path"] if record else None

    if record:
        if v_path and v_path != record["ga_image_path"]:
            delete_file_if_exists(UPLOAD_ROOT, record["ga_image_path"])
        if f_path and f_path != record["image2_image_path"]:
            delete_file_if_exists(UPLOAD_ROOT, record["image2_image_path"])
        
        for idx in range(3, 7):
            p_key = f"img{idx}_path"
            if paths[p_key] and paths[p_key] != record[p_key]:
                delete_file_if_exists(UPLOAD_ROOT, record[p_key])
        
        # Finally, call the update procedure
        result = db.execute(
            text("CALL sp_UpdateFrameOuter(:id, :ga_ref, :status, :ga_img, :img2, :img3, :img4, :img5, :img6, :remarks, :eid)"),
            {
                "id": record_id,
                "ga_ref": ga_reference.strip() if ga_reference else record["ga_reference"],
                "status": record["status"],
                "ga_img": v_path,
                "img2": f_path,
                "img3": paths.get("img3_path"),
                "img4": paths.get("img4_path"),
                "img5": paths.get("img5_path"),
                "img6": paths.get("img6_path"),
                "remarks": remarks.strip() if remarks and remarks.strip() else record["remarks"],
                "eid": str(emp_id)
            }
        ).mappings().first()
    else:
        result = db.execute(
            text("CALL sp_CreateFrameOuter(:ga_ref, :ga_img, :img2, :img3, :img4, :img5, :img6, :remarks, :eid)"),
            {
                "ga_ref": ga_reference.strip() if ga_reference else None,
                "ga_img": v_path,
                "img2": f_path,
                "img3": paths.get("img3_path"),
                "img4": paths.get("img4_path"),
                "img5": paths.get("img5_path"),
                "img6": paths.get("img6_path"),
                "remarks": remarks.strip() if remarks and remarks.strip() else None,
                "eid": str(emp_id)
            }
        ).mappings().first()
    
    db.commit()
    return {"success": True, "data": serialize_ga_obj(result)}

# --- UPDATE (PUT by ID) ---
@router.put("/{id}")
def update_ga(
    id: int,
    status: Optional[int] = Form(None),
    ga_image_path: Optional[UploadFile] = File(None),
    image2_image_path: Optional[UploadFile] = File(None),
    valve_label_file: Optional[UploadFile] = File(None),
    tank_frame_file: Optional[UploadFile] = File(None),
    ga_file: Optional[UploadFile] = File(None),
    image2_file: Optional[UploadFile] = File(None),
    img3_file: Optional[UploadFile] = File(None),
    img4_file: Optional[UploadFile] = File(None),
    img5_file: Optional[UploadFile] = File(None),
    img6_file: Optional[UploadFile] = File(None),
    remarks: Optional[str] = Form(None),
    ga_reference: Optional[str] = Form(None),
    clear_valve_label: Optional[str] = Form(None),
    clear_tank_frame: Optional[str] = Form(None),
    clear_img3: Optional[str] = Form(None),
    clear_img4: Optional[str] = Form(None),
    clear_img5: Optional[str] = Form(None),
    clear_img6: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    emp_id: str = Depends(get_emp_id_from_token)
):
    record = db.execute(text("CALL sp_GetFrameOuterById(:id)"), {"id": id}).mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    tank_no = "GLOBAL"
    upd = dict(record)

    # Handle status
    if status is not None:
        upd["status"] = 1 if int(status) == 1 else 0

    if remarks is not None:
        upd["remarks"] = remarks.strip() if remarks and remarks.strip() else None

    if ga_reference is not None:
        ref = ga_reference.strip() if ga_reference else None
        if ref:
            other = db.execute(text("SELECT id FROM tank_frame_outer WHERE ga_reference = :ref AND id <> :id LIMIT 1"), {"ref": ref, "id": id}).mappings().first()
            if other:
                raise HTTPException(status_code=400, detail="This GA Reference already exists.")
        upd["ga_reference"] = ref

    # Handle clears
    if clear_valve_label == '1':
        delete_file_if_exists(UPLOAD_ROOT, upd["ga_image_path"])
        upd["ga_image_path"] = None
    
    if clear_tank_frame == '1':
        delete_file_if_exists(UPLOAD_ROOT, upd["image2_image_path"])
        upd["image2_image_path"] = None

    # Handle replacement uploads
    if ga_image_path and ga_image_path.filename:
        delete_file_if_exists(UPLOAD_ROOT, upd["ga_image_path"])
        upd["ga_image_path"] = save_uploaded_file(ga_image_path, tank_no, "valve_label", UPLOAD_ROOT)
    elif valve_label_file and valve_label_file.filename:
        delete_file_if_exists(UPLOAD_ROOT, upd["ga_image_path"])
        upd["ga_image_path"] = save_uploaded_file(valve_label_file, tank_no, "valve_label", UPLOAD_ROOT)
    elif ga_file and ga_file.filename:
        delete_file_if_exists(UPLOAD_ROOT, upd["ga_image_path"])
        upd["ga_image_path"] = save_uploaded_file(ga_file, tank_no, "valve_label", UPLOAD_ROOT)
    
    if image2_image_path and image2_image_path.filename:
        delete_file_if_exists(UPLOAD_ROOT, upd["image2_image_path"])
        upd["image2_image_path"] = save_uploaded_file(image2_image_path, tank_no, "tank_frame", UPLOAD_ROOT)
    elif tank_frame_file and tank_frame_file.filename:
        delete_file_if_exists(UPLOAD_ROOT, upd["image2_image_path"])
        upd["image2_image_path"] = save_uploaded_file(tank_frame_file, tank_no, "tank_frame", UPLOAD_ROOT)
    elif image2_file and image2_file.filename:
        delete_file_if_exists(UPLOAD_ROOT, upd["image2_image_path"])
        upd["image2_image_path"] = save_uploaded_file(image2_file, tank_no, "tank_frame", UPLOAD_ROOT)

    # Handle 4 additional images
    for idx in range(3, 7):
        f_obj = locals().get(f"img{idx}_file")
        clear_val = locals().get(f"clear_img{idx}")
        p_key = f"img{idx}_path"

        if clear_val == '1':
            delete_file_if_exists(UPLOAD_ROOT, upd[p_key])
            upd[p_key] = None

        if f_obj and f_obj.filename:
            delete_file_if_exists(UPLOAD_ROOT, upd[p_key])
            upd[p_key] = save_uploaded_file(f_obj, tank_no, f"valve_img{idx}", UPLOAD_ROOT)

    # Finally, call the update procedure
    result = db.execute(
        text("CALL sp_UpdateFrameOuter(:id, :ga_ref, :status, :ga_img, :img2, :img3, :img4, :img5, :img6, :remarks, :eid)"),
        {
            "id": id,
            "ga_ref": upd["ga_reference"],
            "status": upd["status"],
            "ga_img": upd["ga_image_path"],
            "img2": upd["image2_image_path"],
            "img3": upd.get("img3_path"),
            "img4": upd.get("img4_path"),
            "img5": upd.get("img5_path"),
            "img6": upd.get("img6_path"),
            "remarks": upd["remarks"],
            "eid": str(emp_id)
        }
    ).mappings().first()
    
    db.commit()
    return {"success": True, "message": "Updated successfully"}

# --- DELETE ---
@router.delete("/{id}")
def delete_ga(id: int, db: Session = Depends(get_db)):
    record = db.execute(text("CALL sp_GetFrameOuterById(:id)"), {"id": id}).mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    
    delete_file_if_exists(UPLOAD_ROOT, record["ga_image_path"])
    delete_file_if_exists(UPLOAD_ROOT, record["image2_image_path"])
    for idx in range(3, 7):
        delete_file_if_exists(UPLOAD_ROOT, record[f"img{idx}_path"])
    
    db.execute(text("CALL sp_DeleteFrameOuter(:id)"), {"id": id})
    db.commit()
    return {"success": True, "message": "Deleted successfully"}
