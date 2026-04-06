from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.database import get_db
from app.models.tank_certificate import TankCertificate
from app.models.tank_header import Tank
import os
from typing import Optional, Union
from datetime import date as date_type, datetime
import re
import traceback
import logging

from app.utils.upload_utils import save_uploaded_file, delete_file_if_exists
from app.utils.s3_utils import to_cdn_url
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

try:
    from app.models.users_model import User
except Exception:
    User = None


def get_emp_id_from_token(authorization: Optional[str]) -> str:
    """Soft auth: parse emp_id from Bearer token. Returns 'System' on any failure."""
    if not authorization:
        return "System"
    try:
        auth = authorization.strip()
        token = auth[7:].strip() if auth.lower().startswith("bearer") else auth
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        emp_id = payload.get("emp_id")
        return str(int(emp_id)) if emp_id else "System"
    except Exception:
        return "System"

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_ROOT = os.getenv(
    "UPLOAD_ROOT",
    os.path.join(os.path.dirname(__file__), ".", ".", "uploads"),
)

CERTIFICATE_TYPE = "certificates"

# Max PDF size: 2 MB
MAX_PDF_SIZE = 2 * 1024 * 1024
ALLOWED_PDF_TYPES = {"application/pdf"}


# --- HELPERS ---

def validate_pdf(upload_file: UploadFile, field_label: str):
    """Validate that file is PDF and ≤ 2 MB."""
    content_type = getattr(upload_file, "content_type", "") or ""
    if content_type.lower() not in ALLOWED_PDF_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_label}: Only PDF files are allowed (got '{content_type}')."
        )
    contents = upload_file.file.read()
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"{field_label}: File size exceeds 2 MB ({len(contents) // 1024} KB)."
        )
    upload_file.file.seek(0)


def clean_form_data(value: Optional[str]):
    return value.strip() if value else None


def safe_serialize_date(date_value: Union[date_type, datetime, str, None]) -> Optional[str]:
    if isinstance(date_value, str):
        return date_value
    if date_value and isinstance(date_value, (date_type, datetime)):
        return date_value.strftime("%Y/%m")
    return None


def _normalize_date_str(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip().replace('-', '/')
    m = re.match(r'^(\d{4})/(\d{2})/(\d{2})$', s)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m2 = re.match(r'^(\d{4})/(\d{2})$', s)
    if m2:
        mm = int(m2.group(2))
        if 1 <= mm <= 12:
            return f"{m2.group(1)}/{m2.group(2)}"
    return None


def to_url(raw):
    if not raw:
        return ""
    return to_cdn_url(raw) if "://" not in raw else raw


def serialize_certificate(cert):
    return {
        "id": cert.id,
        "tank_id": cert.tank_id,
        "tank_number": getattr(cert, "tank_number", "") or "",
        "certificate_number": cert.certificate_number,
        "insp_2_5y_date": safe_serialize_date(cert.insp_2_5y_date),
        "next_insp_date": safe_serialize_date(cert.next_insp_date),
        "year_of_manufacturing": getattr(cert, "year_of_manufacturing", "") or "",
        "inspection_agency": getattr(cert, "inspection_agency", "") or "",
        "status": getattr(cert, "status", 1),
        # PDF file URLs
        "periodic_inspection_pdf_path": to_url(getattr(cert, "periodic_inspection_pdf_path", None)),
        "periodic_inspection_pdf_name": getattr(cert, "periodic_inspection_pdf_name", None),
        "next_insp_pdf_path": to_url(getattr(cert, "next_insp_pdf_path", None)),
        "next_insp_pdf_name": getattr(cert, "next_insp_pdf_name", None),
        "new_certificate_file": to_url(getattr(cert, "new_certificate_file", None)),
        "new_certificate_file_name": getattr(cert, "new_certificate_file_name", None),
        "old_certificate_file": to_url(getattr(cert, "old_certificate_file", None)),
        "old_certificate_file_name": getattr(cert, "old_certificate_file_name", None),
        "created_by": cert.created_by,
        "updated_by": getattr(cert, "updated_by", None),
        "created_at": cert.created_at.isoformat() if cert.created_at else None,
        "updated_at": cert.updated_at.isoformat() if cert.updated_at else None,
    }


def save_pdf(upload_file: Optional[UploadFile], label: str, image_type: str, tank_number: str) -> tuple:
    """Validate, save a PDF file and return (path, filename). Returns (None, None) if no file."""
    if not upload_file or not upload_file.filename:
        return None, None
    validate_pdf(upload_file, label)
    path = save_uploaded_file(
        upload_file=upload_file,
        tank_number=tank_number,
        image_type=image_type,
        upload_root=UPLOAD_ROOT,
    )
    return path, upload_file.filename


# -------- LIST ALL --------
@router.get("/")
def get_all_certificates(db: Session = Depends(get_db)):
    certs = db.query(TankCertificate).all()
    return [serialize_certificate(c) for c in certs]


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
        return [serialize_certificate(c) for c in certificates]
    except OperationalError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database schema error.")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error retrieving certificates")


# -------- READ BY ID --------
@router.get("/{cert_id}")
def get_tank_certificate_by_id(cert_id: int, db: Session = Depends(get_db)):
    cert = db.query(TankCertificate).filter(TankCertificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Tank certificate not found")
    return serialize_certificate(cert)


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
    # 4 PDF uploads
    periodic_inspection_pdf: Optional[UploadFile] = File(None),
    next_insp_pdf: Optional[UploadFile] = File(None),
    new_certificate_file: Optional[UploadFile] = File(None),
    old_certificate_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    if path_tank_id is not None:
        tank_id = path_tank_id
    if tank_id is None:
        raise HTTPException(status_code=400, detail="tank_id is required")

    tank_record = db.query(Tank).filter(Tank.id == tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Tank not found")

    existing_cert = db.query(TankCertificate).filter(TankCertificate.tank_id == tank_id).first()
    if existing_cert:
        raise HTTPException(
            status_code=400,
            detail="A certificate already exists for this tank. Please edit the existing one."
        )

    tank_number = tank_record.tank_number

    if not certificate_number or not certificate_number.strip():
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        certificate_number = f"CERT-{tank_number}-{ts}"

    emp_id = get_emp_id_from_token(authorization)

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
    year_of_manufacturing = None
    try:
        from app.models.tank_details import TankDetails
        tank_details = db.query(TankDetails).filter(TankDetails.tank_id == tank_id).first()
        year_of_manufacturing = tank_details.date_mfg if tank_details else None
    except Exception:
        pass

    # Save PDFs
    try:
        p_path, p_name = save_pdf(periodic_inspection_pdf, "Periodic Inspection PDF", "cert_periodic", tank_number)
        n_path, n_name = save_pdf(next_insp_pdf, "Next Inspection PDF", "cert_next_insp", tank_number)
        nc_path, nc_name = save_pdf(new_certificate_file, "New Certificate PDF", "cert_new", tank_number)
        oc_path, oc_name = save_pdf(old_certificate_file, "Old Certificate PDF", "cert_old", tank_number)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    try:
        cert = TankCertificate(
            tank_id=tank_id,
            tank_number=tank_number,
            certificate_number=clean_form_data(certificate_number),
            insp_2_5y_date=_normalize_date_str(insp_2_5y_date),
            next_insp_date=_normalize_date_str(next_insp_date),
            inspection_agency=inspection_agency_name,
            year_of_manufacturing=year_of_manufacturing,
            periodic_inspection_pdf_path=p_path,
            periodic_inspection_pdf_name=p_name,
            next_insp_pdf_path=n_path,
            next_insp_pdf_name=n_name,
            new_certificate_file=nc_path,
            new_certificate_file_name=nc_name,
            old_certificate_file=oc_path,
            old_certificate_file_name=oc_name,
            status=1,
            created_by=emp_id,
            updated_by=emp_id,
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)
    except OperationalError as op_err:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database mismatch: A column might be missing.")
    except Exception as e:
        db.rollback()
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Database Insertion Failed: {str(e)}")

    # Sync next inspection date to tank_inspection_details
    try:
        from sqlalchemy import text
        db.execute(
            text("UPDATE tank_inspection_details SET pi_next_inspection_date = :next_date WHERE tank_number = :tank_num"),
            {"next_date": cert.next_insp_date, "tank_num": tank_number}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to sync pi_next_inspection_date: {str(e)}")

    return {"message": "Tank certificate added successfully", "data": serialize_certificate(cert)}


# -------- UPDATE --------
@router.put("/{cert_id}")
def update_tank_certificate(
    cert_id: int,
    certificate_number: Optional[str] = Form(None),
    insp_2_5y_date: Optional[str] = Form(None),
    next_insp_date: Optional[str] = Form(None),
    inspection_agency_id: Optional[int] = Form(None),
    status: Optional[int] = Form(None),
    # 4 PDF uploads
    periodic_inspection_pdf: Optional[UploadFile] = File(None),
    next_insp_pdf: Optional[UploadFile] = File(None),
    new_certificate_file: Optional[UploadFile] = File(None),
    old_certificate_file: Optional[UploadFile] = File(None),
    # Clear flags — send '1' to remove an existing file
    clear_periodic_inspection_pdf: Optional[str] = Form(None),
    clear_next_insp_pdf: Optional[str] = Form(None),
    clear_new_certificate_file: Optional[str] = Form(None),
    clear_old_certificate_file: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    cert = db.query(TankCertificate).filter(TankCertificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Tank certificate not found")

    emp_id = get_emp_id_from_token(authorization)

    tank_record = db.query(Tank).filter(Tank.id == cert.tank_id).first()
    tank_number = tank_record.tank_number if tank_record else "UNKNOWN"

    if certificate_number is not None:
        cert.certificate_number = clean_form_data(certificate_number)
    if insp_2_5y_date is not None:
        n = _normalize_date_str(insp_2_5y_date)
        if n:
            cert.insp_2_5y_date = n
    if next_insp_date is not None:
        n = _normalize_date_str(next_insp_date)
        if n:
            cert.next_insp_date = n
    if status is not None:
        cert.status = 1 if int(status) == 1 else 0
    if inspection_agency_id is not None:
        try:
            from app.models.inspection_agency_master_model import InspectionAgencyMaster
            agency = db.query(InspectionAgencyMaster).filter_by(id=inspection_agency_id).first()
            if not agency:
                raise HTTPException(status_code=400, detail=f"inspection_agency_id '{inspection_agency_id}' is not valid")
            cert.inspection_agency = agency.agency_name
        except HTTPException:
            raise
        except Exception:
            pass

    # Handle PDF updates
    try:
        # --- Clear requests (remove existing file, null DB field) ---
        if clear_periodic_inspection_pdf == '1':
            if cert.periodic_inspection_pdf_path:
                delete_file_if_exists(UPLOAD_ROOT, cert.periodic_inspection_pdf_path)
            cert.periodic_inspection_pdf_path = None
            cert.periodic_inspection_pdf_name = None

        if clear_next_insp_pdf == '1':
            if cert.next_insp_pdf_path:
                delete_file_if_exists(UPLOAD_ROOT, cert.next_insp_pdf_path)
            cert.next_insp_pdf_path = None
            cert.next_insp_pdf_name = None

        if clear_new_certificate_file == '1':
            if cert.new_certificate_file:
                delete_file_if_exists(UPLOAD_ROOT, cert.new_certificate_file)
            cert.new_certificate_file = None
            cert.new_certificate_file_name = None

        if clear_old_certificate_file == '1':
            if cert.old_certificate_file:
                delete_file_if_exists(UPLOAD_ROOT, cert.old_certificate_file)
            cert.old_certificate_file = None
            cert.old_certificate_file_name = None

        # --- New file uploads (replace) ---
        if periodic_inspection_pdf and periodic_inspection_pdf.filename:
            if cert.periodic_inspection_pdf_path:
                delete_file_if_exists(UPLOAD_ROOT, cert.periodic_inspection_pdf_path)
            p, n = save_pdf(periodic_inspection_pdf, "Periodic Inspection PDF", "cert_periodic", tank_number)
            cert.periodic_inspection_pdf_path = p
            cert.periodic_inspection_pdf_name = n

        if next_insp_pdf and next_insp_pdf.filename:
            if cert.next_insp_pdf_path:
                delete_file_if_exists(UPLOAD_ROOT, cert.next_insp_pdf_path)
            p, n = save_pdf(next_insp_pdf, "Next Inspection PDF", "cert_next_insp", tank_number)
            cert.next_insp_pdf_path = p
            cert.next_insp_pdf_name = n

        if new_certificate_file and new_certificate_file.filename:
            if cert.new_certificate_file:
                delete_file_if_exists(UPLOAD_ROOT, cert.new_certificate_file)
            p, n = save_pdf(new_certificate_file, "New Certificate PDF", "cert_new", tank_number)
            cert.new_certificate_file = p
            cert.new_certificate_file_name = n

        if old_certificate_file and old_certificate_file.filename:
            if cert.old_certificate_file:
                delete_file_if_exists(UPLOAD_ROOT, cert.old_certificate_file)
            p, n = save_pdf(old_certificate_file, "Old Certificate PDF", "cert_old", tank_number)
            cert.old_certificate_file = p
            cert.old_certificate_file_name = n

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File update failed: {str(e)}")

    cert.updated_by = emp_id

    try:
        db.commit()
        db.refresh(cert)
    except OperationalError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database schema mismatch during update.")
    except Exception as e:
        db.rollback()
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Database Update Failed: {str(e)}")

    try:
        from sqlalchemy import text
        db.execute(
            text("UPDATE tank_inspection_details SET pi_next_inspection_date = :next_date WHERE tank_number = :tank_num"),
            {"next_date": cert.next_insp_date, "tank_num": tank_number}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to sync pi_next_inspection_date on update: {str(e)}")

    return {"message": "Tank certificate updated successfully", "data": serialize_certificate(cert)}


# -------- DELETE --------
@router.delete("/{cert_id}")
def delete_tank_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    cert = db.query(TankCertificate).filter(TankCertificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Tank certificate not found")

    for field in ["periodic_inspection_pdf_path", "next_insp_pdf_path", "new_certificate_file", "old_certificate_file"]:
        p = getattr(cert, field, None)
        if p:
            delete_file_if_exists(UPLOAD_ROOT, p)

    db.delete(cert)
    db.commit()
    return {"message": "Tank certificate deleted successfully"}
