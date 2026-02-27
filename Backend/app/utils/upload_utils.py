
import logging
from typing import Dict, Optional
from fastapi import UploadFile, HTTPException, status
from io import BytesIO
from app.utils.s3_utils import build_s3_key, upload_fileobj_to_s3, delete_s3_object
import os
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

# Image type definitions
# (I have kept your existing list, but the logic works for any type you add)
IMAGE_TYPES: Dict[str, str] = {
    "frontview": "Front View",
    "rearview": "Rear View",
    "topview": "Top View",
    "undersideview": "Underside View",
    "frontlhview": "Front Left Hand View",
    "rearlhview": "Rear Left Hand View",
    "frontrhview": "Front Right Hand View",
    "rearrhview": "Rear Right Hand View",
    "lhsideview": "Left Hand Side View",
    "rhsideview": "Right Hand Side View",
    "valvessectionview": "Valves Section View",
    "safetyvalve": "Safety Valve",
    "levelpressuregauge": "Level Pressure Gauge",
    "vacuumreading": "Vacuum Reading",
    "certificate": "Certificate",
    "drawings": "Drawings",
    "valve_report": "Valve Report",
}

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"} 
# Added PDF just in case for reports/certificates, remove if strictly images only.

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB default


def validate_image_type(image_type: str) -> str:
    """Validate and normalize image type to lowercase."""
    normalized = image_type.lower() if image_type else ""
    if normalized not in IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image_type '{image_type}'. Allowed types: {', '.join(IMAGE_TYPES.keys())}"
        )
    return normalized


def validate_file_content_type(file: UploadFile) -> None:
    """Validate file content type and basic file validation."""
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type not provided"
        )
    
    # Optional: Allow PDF if you are doing certificates/reports
    if not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Got: {file.content_type}"
        )
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not supported. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
        )


def get_file_extension(filename: str) -> str:
    """Extract and validate file extension."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is empty"
        )
    
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        # Default fallback
        ext = ".jpg"
    
    return ext



def save_uploaded_file(
    upload_file: UploadFile,
    tank_number: str,
    image_type: str,
    upload_root: str,
    max_size: int = MAX_UPLOAD_SIZE
) -> str:
    """
    Save uploaded file to S3. Returns S3 key.
    """
    try:
        validate_file_content_type(upload_file)
        ext = get_file_extension(upload_file.filename)
        # Clean logical filename
        logical_name = f"{tank_number}_{image_type}{ext}"
        s3_key = build_s3_key(logical_name)
        # Read file into BytesIO
        buffer = BytesIO()
        bytes_written = 0
        chunk_size = 65536
        while True:
            chunk = upload_file.file.read(chunk_size)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds limit"
                )
            buffer.write(chunk)
        buffer.seek(0)
        upload_fileobj_to_s3(buffer, s3_key, upload_file.content_type)
        upload_file.file.close()
        return s3_key
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error")



def delete_file_if_exists(upload_root: str, stored_path: str) -> None:
    """
    Delete file from S3. If stored_path contains a URL, strip domain and use S3 key.
    """
    try:
        key = stored_path
        if not key:
            return
        if "://" in key:
            # Strip domain, keep only S3 key
            key = key.split("/", 3)[-1]
        delete_s3_object(key)
    except Exception as e:
        logger.error(f"Error deleting S3 object {stored_path}: {str(e)}")


def cleanup_temp_files(upload_root: str, hours_old: int = 2) -> int:
    """
    Clean up temporary files older than specified hours.
    """
    tmp_dir = os.path.join(upload_root, "tmp")
    if not os.path.exists(tmp_dir):
        return 0
    
    deleted_count = 0
    cutoff_time = datetime.now() - timedelta(hours=hours_old)
    
    try:
        for filename in os.listdir(tmp_dir):
            file_path = os.path.join(tmp_dir, filename)
            if os.path.isfile(file_path):
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {filename}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cleaning temp directory: {str(e)}")
    
    return deleted_count