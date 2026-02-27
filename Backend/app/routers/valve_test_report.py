from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.valve_test_report import ValveTestReport 
from app.models.tank_header import Tank
import os
from typing import Optional
from datetime import date as date_type
from typing import Optional
import os
import jwt
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

try:
    from app.models.users_model import User
except Exception:
    User = None

# Import shared utility functions
from app.utils.upload_utils import save_uploaded_file, delete_file_if_exists
from datetime import datetime

def parse_test_date(date_str: Optional[str]) -> Optional[date_type]:
    """
    Parse test_date from string.
    Accepts: 'YYYY-MM-DD' or 'YYYY/MM/DD' (and some common variants).
    """
    if not date_str:
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # First, normalize slashes to dashes: 2025/12/20 -> 2025-12-20
    normalized = date_str.replace("/", "-")

    # Try ISO first: YYYY-MM-DD
    try:
        return date_type.fromisoformat(normalized)
    except ValueError:
        pass

    # Fallback to a few common patterns if needed
    for fmt in ("%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # If nothing matched, treat as invalid input
    raise HTTPException(
        status_code=400,
        detail="Invalid date format for test_date. Use YYYY-MM-DD or YYYY/MM/DD.",
    )

router = APIRouter()

# Get upload root from environment or default
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
## S3 migration: UPLOAD_ROOT is unused for new uploads, kept for compatibility

# Fixed Image Type for this router
VALVE_REPORT_TYPE = "valve_reports"

def clean_form_data(value: Optional[str]):
    return value.strip() if value else None
from fastapi import HTTPException
# TODO: change this to your actual JWT decode util
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


# --- CREATE ---
@router.post("/")
def create_valve_test_report(
    tank_id: int = Form(...),
    test_date: Optional[str] = Form(None),
    inspected_by: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    inspection_report_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: str = Header(...)
):

    # 1. Fetch Tank to get tank_number
    tank_record = db.query(Tank).filter(Tank.id == tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    tank_number = tank_record.tank_number

    # 2. Save File
    file_path_db = None
    if inspection_report_file:
        try:
            file_path_db = save_uploaded_file(
                upload_file=inspection_report_file,
                tank_number=tank_number,
                image_type=VALVE_REPORT_TYPE,
                upload_root=UPLOAD_ROOT
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    parsed_date = parse_test_date(test_date)

        # Get emp_id of logged-in user from token
    emp_id = get_emp_id_from_token(authorization)
    try:
        new_report = ValveTestReport(
            tank_id=tank_id,
            test_date=parsed_date,
            inspected_by=clean_form_data(inspected_by),
            remarks=clean_form_data(remarks),
            inspection_report_file=file_path_db,
            created_by=emp_id
        )

        db.add(new_report)
        db.commit()
        db.refresh(new_report)
    except Exception as e:
        db.rollback()
        # Cleanup file if DB insertion fails
        if file_path_db:
            delete_file_if_exists(UPLOAD_ROOT, file_path_db)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Report created successfully", "data": new_report}

# --- READ BY TANK ID ---
@router.get("/tank/{tank_id}")
def get_valve_reports_by_tank(tank_id: int, db: Session = Depends(get_db)):
    reports = db.query(ValveTestReport).filter(ValveTestReport.tank_id == tank_id).order_by(ValveTestReport.created_at.desc()).all()
    return reports

# --- UPDATE ---

@router.put("/{report_id}")

def update_valve_test_report(
    report_id: int,
    test_date: Optional[str] = Form(None),
    inspected_by: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    inspection_report_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    authorization: str = Header(...)
):
        # Get emp_id of logged-in user from token
    emp_id = get_emp_id_from_token(authorization)
    report = db.query(ValveTestReport).filter(ValveTestReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Fetch Tank Number for file operations
    tank_record = db.query(Tank).filter(Tank.id == report.tank_id).first()
    if not tank_record:
        raise HTTPException(status_code=404, detail="Associated Tank not found")
    
    tank_number = tank_record.tank_number

    # File Update Logic
    if inspection_report_file:
        # 1. Delete old file if exists
        if report.inspection_report_file:
            delete_file_if_exists(UPLOAD_ROOT, report.inspection_report_file)
        
        # 2. Save new file
        try:
            new_file_path = save_uploaded_file(
                upload_file=inspection_report_file,
                tank_number=tank_number,
                image_type=VALVE_REPORT_TYPE,
                upload_root=UPLOAD_ROOT
            )
            report.inspection_report_file = new_file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    if test_date is not None:
        report.test_date = parse_test_date(test_date)

    if inspected_by is not None:
        report.inspected_by = clean_form_data(inspected_by)
    if remarks is not None:
        report.remarks = clean_form_data(remarks)

    report.updated_by = emp_id

    try:
        db.commit()
        db.refresh(report)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update error: {str(e)}")

    return {"message": "Report updated successfully", "data": report}

# --- DELETE ---
@router.delete("/{report_id}")
def delete_valve_test_report(report_id: int, db: Session = Depends(get_db), authorization: str = Header(...)):
    """Deletes a valve test report and its associated file."""
    report = db.query(ValveTestReport).filter(ValveTestReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Delete associated file and cleanup folders
    if report.inspection_report_file:
        delete_file_if_exists(UPLOAD_ROOT, report.inspection_report_file)

    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully"}