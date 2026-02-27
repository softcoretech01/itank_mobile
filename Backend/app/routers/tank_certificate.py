from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.database import get_db
from app.models.tank_certificate import TankCertificate
from app.models.tank_header import Tank
import os
import shutil
import uuid
from typing import Optional, Union
from datetime import date as date_type, datetime
import re
import traceback
import logging

# Import your shared utility functions
from app.utils.upload_utils import save_uploaded_file, delete_file_if_exists
from app.utils.s3_utils import to_cdn_url
from app.routers.tank_inspection_router import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Get upload root from environment or default (Same as in your other router)
UPLOAD_ROOT = os.getenv(
    "UPLOAD_ROOT",
    os.path.join(os.path.dirname(__file__), ".", ".", "uploads"),
)
## S3 migration: UPLOAD_ROOT is unused for new uploads, kept for compatibility

# Fixed Image Type for this router
CERTIFICATE_TYPE = "certificates"

# --- HELPERS ---


def clean_form_data(value: Optional[str]):
    return value.strip() if value else None


def safe_serialize_date(date_value: Union[date_type, datetime, str, None]) -> Optional[str]:
    # If already a string (we store YYYY/MM), return as-is
    if isinstance(date_value, str):
        return date_value
    if date_value and isinstance(date_value, (date_type, datetime)):
        # convert date -> YYYY/MM
        return date_value.strftime("%Y/%m")
    return None


def _normalize_date_str(s: Optional[str]) -> Optional[str]:
    """
    Accepts inputs like 'YYYY-MM', 'YYYY/MM', 'YYYY-MM-DD', 'YYYY/MM/DD'
    and normalize them to 'YYYY/MM' (year/month) string format.
    """
    if not s:
        return None
    s = s.strip()
    # unify separators to '/'
    s = s.replace('-', '/')

    # If full date given (YYYY/MM/DD), reduce to YYYY/MM
    m = re.match(r'^(\d{4})/(\d{2})/(\d{2})$', s)
    if m:
        return f"{m.group(1)}/{m.group(2)}"

    # If year/month given (YYYY/MM) accept as-is if month 01-12
    m2 = re.match(r'^(\d{4})/(\d{2})$', s)
    if m2:
        mm = int(m2.group(2))
        if 1 <= mm <= 12:
            return f"{m2.group(1)}/{m2.group(2)}"

    # If only year provided (YYYY), return None (not valid for this field)
    return None


def map_form_to_payload(
    tank_id: int,
    certificate_number: str,
    insp_2_5y_date: Optional[str] = None,
    next_insp_date: Optional[str] = None,
    inspection_agency: Optional[str] = None,
    year_of_manufacturing: Optional[str] = None,
    created_by: Optional[str] = "System",
    existing_file_path: Optional[str] = None,
):
    insp_2_5y_date = _normalize_date_str(insp_2_5y_date)
    next_insp_date = _normalize_date_str(next_insp_date)

    return {
        "tank_id": tank_id,
        "certificate_number": clean_form_data(certificate_number),
        # store normalized YYYY/MM strings (or None)
        "insp_2_5y_date": insp_2_5y_date,
        "next_insp_date": next_insp_date,
        "inspection_agency": clean_form_data(inspection_agency),
        "year_of_manufacturing": year_of_manufacturing,
        "created_by": clean_form_data(created_by),
        "certificate_file": existing_file_path,
    }




@router.post("/upload-certificate-image")
def upload_certificate_image(file: UploadFile = File(...)):
    """
    Generic endpoint to upload certificate-related images (periodic, next_insp).
    """
    try:
        from app.utils.s3_utils import build_s3_key, upload_fileobj_to_s3
        
        file_ext = os.path.splitext(file.filename)[1]
        s3_key = build_s3_key(file.filename)
        
        upload_fileobj_to_s3(file.file, s3_key, file.content_type)
            
        return {"path": s3_key} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image to S3: {str(e)}")


# -------- CREATE --------
@router.post("/")
@router.post("/{path_tank_id}")
def create_tank_certificate(
    path_tank_id: Optional[int] = None,
    tank_id: Optional[int] = Form(None),
    certificate_number: Optional[str] = Form(None),
    insp_2_5y_date: Optional[str] = Form(None),
    next_insp_date: Optional[str] = Form(None),
    inspection_agency_id: Optional[int] = Form(None),
    periodic_inspection_image_path: Optional[str] = Form(None),
    next_insp_image_path: Optional[str] = Form(None),
    certificate_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None),
):
    # Support tank_id from either Form or URL path
    if path_tank_id is not None:
        tank_id = path_tank_id

    if tank_id is None:
         raise HTTPException(status_code=400, detail="tank_id is required")

    # 1. Fetch Tank FIRST to get the tank_number for folder structure
    tank_record = db.query(Tank).filter(Tank.id == tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Tank not found")

    tank_number = tank_record.tank_number

    # 2. Auto-generate certificate_number if missing (prevents 400 error)
    if not certificate_number or not certificate_number.strip():
        # Fallback: FILE-TankNo-Timestamp
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        certificate_number = f"CERT-{tank_number}-{ts}"

    # Get emp_id from the logged-in user
    emp_id = "System"
    if current_user and hasattr(current_user, "emp_id"):
        emp_id = str(current_user.emp_id)

    # 3. Handle File Upload using shared utility
    file_path_db = None
    if certificate_file:
        try:
            file_path_db = save_uploaded_file(
                upload_file=certificate_file,
                tank_number=tank_number,
                image_type=CERTIFICATE_TYPE,
                upload_root=UPLOAD_ROOT,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"File upload failed: {str(e)}"
            )

    # Look up inspection agency name
    inspection_agency_name = None
    if inspection_agency_id is not None:
        try:
            from app.models.inspection_agency_master_model import InspectionAgencyMaster
            agency = db.query(InspectionAgencyMaster).filter_by(id=inspection_agency_id).first()
            if agency:
                inspection_agency_name = agency.agency_name
        except Exception:
            pass

    # Fetch year_of_manufacturing
    from app.models.tank_details import TankDetails
    tank_details = db.query(TankDetails).filter(TankDetails.tank_id == tank_id).first()
    year_of_manufacturing = tank_details.date_mfg if tank_details else None

    final_payload = map_form_to_payload(
        tank_id=tank_id,
        certificate_number=certificate_number,
        insp_2_5y_date=insp_2_5y_date,
        next_insp_date=next_insp_date,
        inspection_agency=inspection_agency_name,
        year_of_manufacturing=year_of_manufacturing,
        created_by=emp_id,
        existing_file_path=file_path_db,
    )
    
    if periodic_inspection_image_path:
        final_payload["periodic_inspection_image_path"] = periodic_inspection_image_path
    if next_insp_image_path:
        final_payload["next_insp_image_path"] = next_insp_image_path

    # DO NOT include tank_number in constructor args to avoid TypeError
    cleaned_payload = {
        k: v for k, v in final_payload.items() if v is not None or k == "certificate_file"
    }

    try:
        certificate = TankCertificate(**cleaned_payload)

        # If the model actually has a tank_number column, set it here safely
        if hasattr(certificate, "tank_number"):
            certificate.tank_number = tank_number

        db.add(certificate)
        db.commit()
        db.refresh(certificate)
    except OperationalError as op_err:
        db.rollback()
        if file_path_db:
            delete_file_if_exists(UPLOAD_ROOT, file_path_db)
        print(f"DB SCHEMA ERROR: {op_err}")
        raise HTTPException(
            status_code=500,
            detail="Database mismatch: A column might be missing.",
        )
    except Exception as e:
        db.rollback()
        if file_path_db:
            delete_file_if_exists(UPLOAD_ROOT, file_path_db)
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400, detail=f"Database Insertion Failed: {str(e)}"
        )

    return {
        "message": "Tank certificate added successfully",
        "id": certificate.id,
        "file_path": file_path_db,
    }


# -------- READ BY TANK ID --------
@router.get("/tank/{tank_id}")
def get_tank_certificates_by_tank(tank_id: int, db: Session = Depends(get_db)):
    try:
        certificates = (
            db.query(TankCertificate)
            .filter(TankCertificate.tank_id == tank_id)
            .order_by(TankCertificate.created_at.desc())
            .all()
        )

        def serialize_certificate(cert):
            # Turn stored S3 key into a browser-accessible URL
            raw_path = cert.certificate_file or ""
            if raw_path:
                # If it's not already a URL, convert via CDN helper
                file_url = (
                    to_cdn_url(raw_path)
                    if "://" not in raw_path
                    else raw_path
                )
            else:
                file_url = ""

            return {
                "id": cert.id,
                "tank_id": cert.tank_id,
                "certificate_number": cert.certificate_number,
                "insp_2_5y_date": safe_serialize_date(cert.insp_2_5y_date),
                "next_insp_date": safe_serialize_date(cert.next_insp_date),
                "year_of_manufacturing": getattr(
                    cert, "year_of_manufacturing", ""
                )
                or "",
                "inspection_agency": getattr(cert, "inspection_agency", "") or "",
                "certificate_file": file_url,
                "created_at": safe_serialize_date(cert.created_at),
                "created_at": safe_serialize_date(cert.created_at),
                "periodic_inspection_image_path": to_cdn_url(cert.periodic_inspection_image_path) if cert.periodic_inspection_image_path else None,
                "next_insp_image_path": to_cdn_url(cert.next_insp_image_path) if cert.next_insp_image_path else None,
            }

        return [serialize_certificate(cert) for cert in certificates]

    except OperationalError as e:
        print(f"DATABASE OPERATIONAL ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database schema error.")
    except Exception as e:
        print(f"CRITICAL ERROR in get_tank_certificates_by_tank: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error retrieving certificates"
        )


# -------- READ BY ID --------
@router.get("/{cert_id}")
def get_tank_certificate_by_id(cert_id: int, db: Session = Depends(get_db)):
    try:
        cert = (
            db.query(TankCertificate)
            .filter(TankCertificate.id == cert_id)
            .first()
        )
        if not cert:
            raise HTTPException(status_code=404, detail="Tank certificate not found")

        return {
            "id": cert.id,
            "tank_id": cert.tank_id,
            "certificate_number": cert.certificate_number,
            "insp_2_5y_date": safe_serialize_date(cert.insp_2_5y_date),
            "next_insp_date": safe_serialize_date(cert.next_insp_date),
            "year_of_manufacturing": getattr(
                cert, "year_of_manufacturing", ""
            )
            or "",
            "inspection_agency": getattr(cert, "inspection_agency", "") or "",
            "certificate_file": cert.certificate_file or "",
            "created_at": safe_serialize_date(cert.created_at),
        }
    except Exception as e:
        print(f"Fetch error: {e}")
        raise HTTPException(
            status_code=500, detail="Error processing certificate data"
        )


# -------- UPDATE --------
@router.put("/{cert_id}")
def update_tank_certificate(
    cert_id: int,
    certificate_number: Optional[str] = Form(None),
    insp_2_5y_date: Optional[str] = Form(None),
    next_insp_date: Optional[str] = Form(None),
    inspection_agency_id: Optional[int] = Form(None),
    periodic_inspection_image_path: Optional[str] = Form(None),
    next_insp_image_path: Optional[str] = Form(None),
    certificate_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None),  # <- made optional
):
    cert = (
        db.query(TankCertificate)
        .filter(TankCertificate.id == cert_id)
        .first()
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Tank certificate not found")

    # Get emp_id from the logged-in user
    if not current_user or not getattr(current_user, "emp_id", None):
        raise HTTPException(
            status_code=401,
            detail="Could not resolve emp_id from logged-in user"
        )
    emp_id = str(current_user.emp_id)

    # Get Tank Number for file saving
    tank_record = db.query(Tank).filter(Tank.id == cert.tank_id).first()
    if not tank_record:
        raise HTTPException(
            status_code=404, detail="Associated Tank not found"
        )
    tank_number = tank_record.tank_number

    payload = {}
    if certificate_number is not None:
        payload["certificate_number"] = clean_form_data(certificate_number)

    if insp_2_5y_date is not None:
        insp_2_5y_date_norm = _normalize_date_str(insp_2_5y_date)
        if insp_2_5y_date_norm is not None:
            payload["insp_2_5y_date"] = insp_2_5y_date_norm

    if next_insp_date is not None:
        next_insp_date_norm = _normalize_date_str(next_insp_date)
        if next_insp_date_norm is not None:
            payload["next_insp_date"] = next_insp_date_norm

    # Look up inspection agency name from master if inspection_agency_id is provided
    if inspection_agency_id is not None:
        from app.models.inspection_agency_master_model import InspectionAgencyMaster

        agency = (
            db.query(InspectionAgencyMaster)
            .filter_by(id=inspection_agency_id)
            .first()
        )
        if not agency:
            raise HTTPException(
                status_code=400,
                detail=f"inspection_agency_id '{inspection_agency_id}' is not valid",
            )
        payload["inspection_agency"] = agency.agency_name

    payload["updated_by"] = emp_id

    if periodic_inspection_image_path is not None:
         payload["periodic_inspection_image_path"] = periodic_inspection_image_path
    
    if next_insp_image_path is not None:
         payload["next_insp_image_path"] = next_insp_image_path

    # File Update Logic
    if certificate_file:
        # 1. Delete old file if exists
        if cert.certificate_file:
            delete_file_if_exists(UPLOAD_ROOT, cert.certificate_file)

        # 2. Save new file using utility
        try:
            new_file_path = save_uploaded_file(
                upload_file=certificate_file,
                tank_number=tank_number,
                image_type=CERTIFICATE_TYPE,
                upload_root=UPLOAD_ROOT,
            )
            payload["certificate_file"] = new_file_path
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"New file upload failed: {str(e)}",
            )

    try:
        for key, value in payload.items():
            if hasattr(cert, key):
                setattr(cert, key, value)

        db.commit()
        db.refresh(cert)
    except OperationalError as e:
        db.rollback()
        print(f"DB SCHEMA UPDATE ERROR: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database schema mismatch during update.",
        )
    except Exception as e:
        db.rollback()
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400, detail=f"Database Update Failed: {str(e)}"
        )

    return {"message": "Tank certificate updated successfully", "data": cert}


# -------- DELETE --------
@router.delete("/{cert_id}")
def delete_tank_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),  # <- made optional
):
    cert = (
        db.query(TankCertificate)
        .filter(TankCertificate.id == cert_id)
        .first()
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Tank certificate not found")

    # Use utility to delete file and clean up empty folders
    if cert.certificate_file:
        delete_file_if_exists(UPLOAD_ROOT, cert.certificate_file)

    db.delete(cert)
    db.commit()
    return {"message": "Tank certificate deleted successfully"}
