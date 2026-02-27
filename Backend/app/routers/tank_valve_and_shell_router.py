from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tank_valve_and_shell_model import TankValveAndShell
from typing import Optional
from io import BytesIO
import jwt
import os
import uuid
from app.utils.s3_utils import build_s3_key, upload_fileobj_to_s3, to_cdn_url

# Try imports
try:
    from PIL import Image
except ImportError:
    Image = None

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

# Helper for Upload
def process_upload(file: UploadFile, tank_id: int, prefix: str):
    if not file:
        return None, None
        
    # 1. Read
    content = file.file.read()
    file.file.seek(0)
    
    # 2. Build Key
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{tank_id}_{prefix}_{uuid.uuid4().hex}{ext}"
    key = build_s3_key(filename)
    
    # 3. Upload Original (Try S3, then Local)
    buffer = BytesIO(content)
    try:
        upload_fileobj_to_s3(buffer, key, file.content_type)
    except Exception as e:
        print(f"S3 Upload failed (continuing to local): {e}")

    # FORCE LOCAL SAVE (Ensure directory exists)
    local_path = key
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(content)
    except Exception as e:
        print(f"Local save failed: {e}")
    
    # 4. Thumbnail
    thumb_key = None
    if Image:
        try:
            buffer.seek(0)
            with Image.open(buffer) as img:
                img.thumbnail((200, 200))
                thumb_buffer = BytesIO()
                # Convert to RGB if needed (e.g. PNG with alpha)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(thumb_buffer, format="JPEG")
                thumb_buffer.seek(0)
                thumb_name = f"{tank_id}_{prefix}_{uuid.uuid4().hex}_thumb.jpg"
                thumb_key = build_s3_key(thumb_name)
                
                # S3 Thumb
                try:
                    upload_fileobj_to_s3(thumb_buffer, thumb_key, "image/jpeg")
                except:
                    pass
                
                # Local Thumb
                thumb_buffer.seek(0)
                local_thumb_path = thumb_key
                os.makedirs(os.path.dirname(local_thumb_path), exist_ok=True)
                with open(local_thumb_path, "wb") as f:
                    f.write(thumb_buffer.read())
                    
        except Exception as e:
            print(f"Thumbnail failed: {e}")
            thumb_key = key # Fallback
    else:
        thumb_key = key
        
    return key, thumb_key

@router.get("/tank/{tank_id}")
def get_tank_valve_and_shell(tank_id: int, request: Request, db: Session = Depends(get_db)):
    record = db.query(TankValveAndShell).filter(TankValveAndShell.tank_id == tank_id).first()
    
    if not record:
        return {"tank_id": tank_id, "data": None}
    
    def process_url(path):
        if not path:
            return None
        url = to_cdn_url(path)
        if url and not url.startswith("http"):
            base = f"{request.url.scheme}://{request.url.netloc}"
            clean_path = url.lstrip("/")
            url = f"{base}/{clean_path}"
        return url

    return {
        "tank_id": tank_id,
        "data": {
            "id": record.id,
            "valve_label_image_path": record.valve_label_image_path,
            "valve_label_thumbnail_path": record.valve_label_thumbnail_path,
            "tank_frame_image_path": record.tank_frame_image_path,
            "tank_frame_thumbnail_path": record.tank_frame_thumbnail_path,
            "valve_label_image_url": process_url(record.valve_label_image_path),
            "valve_label_thumbnail_url": process_url(record.valve_label_thumbnail_path),
            "tank_frame_image_url": process_url(record.tank_frame_image_path),
            "tank_frame_thumbnail_url": process_url(record.tank_frame_thumbnail_path),
        }
    }

@router.post("/update")
def update_tank_valve_and_shell(
    tank_id: int = Form(...),
    valve_label_file: Optional[UploadFile] = File(None),
    tank_frame_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id(authorization)
    
    record = db.query(TankValveAndShell).filter(TankValveAndShell.tank_id == tank_id).first()
    
    # Process uploads
    valve_key, valve_thumb_key = None, None
    if valve_label_file:
        valve_key, valve_thumb_key = process_upload(valve_label_file, tank_id, "valve_label")
        
    frame_key, frame_thumb_key = None, None
    if tank_frame_file:
        frame_key, frame_thumb_key = process_upload(tank_frame_file, tank_id, "tank_frame")
    
    if record:
        if valve_key:
            record.valve_label_image_path = valve_key
            record.valve_label_thumbnail_path = valve_thumb_key
        if frame_key:
            record.tank_frame_image_path = frame_key
            record.tank_frame_thumbnail_path = frame_thumb_key
        record.modified_by = user_id
    else:
        # Create if not exists
        record = TankValveAndShell(
            tank_id=tank_id,
            valve_label_image_path=valve_key,
            valve_label_thumbnail_path=valve_thumb_key,
            tank_frame_image_path=frame_key,
            tank_frame_thumbnail_path=frame_thumb_key,
            created_by=user_id,
            modified_by=user_id
        )
        db.add(record)
    
    db.commit()
    db.refresh(record)
     
    return {
        "success": True,
        "data": {
            "id": record.id,
            "valve_label_image_url": to_cdn_url(record.valve_label_image_path) if record.valve_label_image_path else None,
            "tank_frame_image_url": to_cdn_url(record.tank_frame_image_path) if record.tank_frame_image_path else None
        }
    }
