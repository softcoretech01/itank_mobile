import os
import logging
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.tank_images_model import TankImages
from app.models.tank_header import Tank
# Ensure these imports match your project structure
from app.utils.upload_utils import (
    IMAGE_TYPES,
    validate_image_type,
    save_uploaded_file,
    delete_file_if_exists
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Get upload root from environment or default
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))

## S3 migration: UPLOAD_ROOT is unused for new uploads, kept for compatibility


# ==================== Pydantic Schemas ====================

class ImageTypeSchema(BaseModel):
    slug: str
    label: str


class ImageTypeResponseSchema(BaseModel):
    success: bool
    data: List[ImageTypeSchema]


class TankImageDataSchema(BaseModel):
    id: Optional[int] = None
    tank_number: str
    image_type: str
    image_label: str
    image_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_date: Optional[str] = None
    uploaded: bool
    filename: Optional[str] = None
    emp_id: Optional[int] = None

    class Config:
        from_attributes = True


class UploadResponseSchema(BaseModel):
    success: bool
    message: str
    data: TankImageDataSchema


class ImagesListResponseSchema(BaseModel):
    success: bool
    data: List[TankImageDataSchema]


class DeleteResponseSchema(BaseModel):
    success: bool
    message: str
    deleted_count: int


# ==================== Helper Functions ====================

def validate_tank(tank_number: str, db: Session) -> Tank:
    """Validate that tank exists in tank_header table."""
    tank = db.query(Tank).filter(Tank.tank_number == tank_number).first()
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank '{tank_number}' not found"
        )
    return tank


def get_image_label(image_type: str) -> str:
    """Get human-readable label for image type."""
    return IMAGE_TYPES.get(image_type, image_type)


def build_image_response(db_record: TankImages) -> TankImageDataSchema:
    """Convert DB record to response schema."""
    return TankImageDataSchema(
        id=db_record.id,
        tank_number=db_record.tank_number,
        image_type=db_record.image_type,
        image_label=get_image_label(db_record.image_type),
        image_path=db_record.image_path,
        created_at=db_record.created_at.isoformat() if db_record.created_at else None,
        updated_at=db_record.updated_at.isoformat() if db_record.updated_at else None,
        created_date=db_record.created_date.isoformat() if db_record.created_date else None,
        uploaded=True,
        filename=os.path.basename(db_record.image_path) if db_record.image_path else None,
        emp_id=db_record.emp_id
    )


def build_empty_image_response(tank_number: str, image_type: str) -> TankImageDataSchema:
    """Build empty response for non-existent image."""
    return TankImageDataSchema(
        id=None,
        tank_number=tank_number,
        image_type=image_type,
        image_label=get_image_label(image_type),
        image_path=None,
        created_at=None,
        updated_at=None,
        created_date=None,
        uploaded=False,
        filename=None,
        emp_id=None
    )


# ==================== Endpoints ====================

@router.get("/types", response_model=ImageTypeResponseSchema, tags=["Upload"])
def get_image_types():
    """Get list of allowed image types."""
    data = [
        ImageTypeSchema(slug=slug, label=label)
        for slug, label in IMAGE_TYPES.items()
    ]
    return ImageTypeResponseSchema(success=True, data=data)


@router.post(
    "/{tank_number}/{image_type}",
    response_model=UploadResponseSchema,
    tags=["Upload"]
)
def upload_image(
    tank_number: str,
    image_type: str,
    file: UploadFile = File(...),
    emp_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Upload or update today's image for a tank and image type.
    """
    try:
        # Validate tank exists
        validate_tank(tank_number, db)
        
        # Validate and normalize image type
        image_type = validate_image_type(image_type)
        
        # Save file to disk (UPDATED LOGIC CALLED HERE)
        image_path = save_uploaded_file(
            file,
            tank_number,
            image_type,
            UPLOAD_ROOT,
            MAX_UPLOAD_SIZE
        )
        
        # Upsert into database
        today = date.today()
        
        existing = db.query(TankImages).filter(
            and_(
                TankImages.tank_number == tank_number,
                TankImages.image_type == image_type,
                TankImages.created_date == today
            )
        ).first()
        
        if existing:
            # Delete old file if it exists and path is different
            # Note: With fixed filenames, path might be same, so we verify
            if existing.image_path and existing.image_path != image_path:
                delete_file_if_exists(UPLOAD_ROOT, existing.image_path)
            
            # Update existing record
            existing.image_path = image_path
            existing.emp_id = emp_id
            existing.updated_at = datetime.now()
            db.commit()
            db.refresh(existing)
            db_record = existing
        else:
            # Create new record
            db_record = TankImages(
                emp_id=emp_id,
                tank_number=tank_number,
                image_type=image_type,
                image_path=image_path,
                created_date=today
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
        
        response_data = build_image_response(db_record)
        return UploadResponseSchema(
            success=True,
            message="Image uploaded successfully",
            data=response_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading image"
        )


@router.put(
    "/{tank_number}/{image_type}",
    response_model=UploadResponseSchema,
    tags=["Upload"]
)
def update_image(
    tank_number: str,
    image_type: str,
    file: UploadFile = File(...),
    emp_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Update today's image for a tank and image type (replace if exists).
    """
    try:
        # Validate tank exists
        validate_tank(tank_number, db)
        
        # Validate and normalize image type
        image_type = validate_image_type(image_type)
        
        today = date.today()
        
        # Check if existing image exists for today
        existing = db.query(TankImages).filter(
            and_(
                TankImages.tank_number == tank_number,
                TankImages.image_type == image_type,
                TankImages.created_date == today
            )
        ).first()
        
        # Save new file first
        # (With fixed filenames, this overwrites the file on disk immediately)
        image_path = save_uploaded_file(
            file,
            tank_number,
            image_type,
            UPLOAD_ROOT,
            MAX_UPLOAD_SIZE
        )
        
        if existing:
            # If path somehow changed (e.g. extension changed), delete old specific file
            if existing.image_path and existing.image_path != image_path:
                delete_file_if_exists(UPLOAD_ROOT, existing.image_path)

            # Update existing record
            existing.image_path = image_path
            existing.emp_id = emp_id
            existing.updated_at = datetime.now()
            db.commit()
            db.refresh(existing)
            db_record = existing
        else:
            # Create new record
            db_record = TankImages(
                emp_id=emp_id,
                tank_number=tank_number,
                image_type=image_type,
                image_path=image_path,
                created_date=today
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
        
        response_data = build_image_response(db_record)
        return UploadResponseSchema(
            success=True,
            message="Image updated successfully",
            data=response_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating image"
        )


@router.get("/{tank_number}/images", response_model=ImagesListResponseSchema, tags=["Upload"])
def get_tank_images(
    tank_number: str,
    image_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all images for a tank."""
    try:
        validate_tank(tank_number, db)
        
        if image_type:
            image_type = validate_image_type(image_type)
        
        query = db.query(TankImages).filter(TankImages.tank_number == tank_number)
        
        if image_type:
            query = query.filter(TankImages.image_type == image_type)
        
        db_records = query.all()
        
        response_data = []
        
        if image_type:
            existing = next((r for r in db_records if r.image_type == image_type), None)
            if existing:
                response_data.append(build_image_response(existing))
            else:
                response_data.append(build_empty_image_response(tank_number, image_type))
        else:
            for type_slug in IMAGE_TYPES.keys():
                existing = next((r for r in db_records if r.image_type == type_slug), None)
                if existing:
                    response_data.append(build_image_response(existing))
                else:
                    response_data.append(build_empty_image_response(tank_number, type_slug))
        
        return ImagesListResponseSchema(success=True, data=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tank images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving images"
        )


@router.delete("/{tank_number}/image", tags=["Upload"])
def delete_image(
    tank_number: str,
    image_type: str = Query(...),
    date_str: str = Query(...),
    db: Session = Depends(get_db)
):
    """Delete a specific image."""
    try:
        validate_tank(tank_number, db)
        image_type = validate_image_type(image_type)
        
        try:
            delete_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        record = db.query(TankImages).filter(
            and_(
                TankImages.tank_number == tank_number,
                TankImages.image_type == image_type,
                TankImages.created_date == delete_date
            )
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found for tank '{tank_number}', type '{image_type}' on {date_str}"
            )
        
        # Delete file from disk (and clean folder if empty)
        if record.image_path:
            delete_file_if_exists(UPLOAD_ROOT, record.image_path)
        
        db.delete(record)
        db.commit()
        
        return DeleteResponseSchema(
            success=True,
            message=f"Image deleted successfully",
            deleted_count=1
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting image"
        )


@router.delete("/{tank_number}/images", tags=["Upload"])
def delete_tank_images(
    tank_number: str,
    date_str: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Delete all images for a tank."""
    try:
        validate_tank(tank_number, db)
        
        query = db.query(TankImages).filter(TankImages.tank_number == tank_number)
        
        if date_str:
            try:
                delete_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                query = query.filter(TankImages.created_date == delete_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        
        records = query.all()
        deleted_count = 0
        
        for record in records:
            if record.image_path:
                delete_file_if_exists(UPLOAD_ROOT, record.image_path)
            db.delete(record)
            deleted_count += 1
        
        db.commit()
        
        return DeleteResponseSchema(
            success=True,
            message=f"Deleted {deleted_count} image(s)",
            deleted_count=deleted_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting images"
        )