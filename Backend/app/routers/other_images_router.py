from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.other_images_model import TankOtherImage
from typing import Optional, List
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

# Helper for Upload (Reused logic)
def process_upload(file: UploadFile, tank_id: int, prefix: str):
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

    # FORCE LOCAL SAVE
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
            thumb_key = key
    else:
        thumb_key = key
        
    return key, thumb_key

@router.get("/tank/{tank_id}")
def get_other_images(tank_id: int, request: Request, db: Session = Depends(get_db)):
    records = db.query(TankOtherImage).filter(TankOtherImage.tank_id == tank_id).all()
    
    result = {}
    if records:
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        
        for r in records:
            img_url = to_cdn_url(r.image_path) if r.image_path else None
            thumb_url = to_cdn_url(r.thumbnail_path) if r.thumbnail_path else None
            
            # Robust URL construction for local
            if img_url and not img_url.startswith("http"):
                clean = img_url.lstrip("/")
                img_url = f"{base_url}/{clean}"
                
            if thumb_url and not thumb_url.startswith("http"):
                clean = thumb_url.lstrip("/")
                thumb_url = f"{base_url}/{clean}"
                
            result[r.image_name] = {
                "id": r.id,
                "image_path": r.image_path,
                "image_url": img_url,
                "thumbnail_url": thumb_url
            }
            
    return {
        "tank_id": tank_id,
        "images": result
    }

@router.post("/update")
def update_other_images(
    tank_id: int = Form(...),
    # Define 9 optional file inputs
    image_1: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    image_6: Optional[UploadFile] = File(None),
    image_7: Optional[UploadFile] = File(None),
    image_8: Optional[UploadFile] = File(None),
    image_9: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id(authorization)
    
    files_map = {
        "image_1": image_1, "image_2": image_2, "image_3": image_3,
        "image_4": image_4, "image_5": image_5, "image_6": image_6,
        "image_7": image_7, "image_8": image_8, "image_9": image_9,
    }
    
    updated_items = {}
    
    for name, file in files_map.items():
        if file:
            # Process upload
            key, thumb_key = process_upload(file, tank_id, f"others_{name}")
            
            # Check exist
            record = db.query(TankOtherImage).filter(
                TankOtherImage.tank_id == tank_id,
                TankOtherImage.image_name == name
            ).first()
            
            if record:
                record.image_path = key
                record.thumbnail_path = thumb_key
                record.modified_by = user_id
            else:
                record = TankOtherImage(
                    tank_id=tank_id,
                    image_name=name,
                    image_path=key,
                    thumbnail_path=thumb_key,
                    created_by=user_id,
                    modified_by=user_id
                )
                db.add(record)
                
            updated_items[name] = key
            
    db.commit()
    
    return {"success": True, "updated": list(updated_items.keys())}
