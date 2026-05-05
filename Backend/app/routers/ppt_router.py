
import traceback
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tank_header import Tank
from app.services.ppt_generator import create_presentation
from pydantic import BaseModel
from datetime import datetime
from io import BytesIO
from app.utils.s3_utils import build_s3_key, upload_fileobj_to_s3, to_cdn_url, clean_filename, PROJECT_NAME
import os
from sqlalchemy import text
import re

router = APIRouter()

## S3 migration: No local save directory needed

class GenerateRequest(BaseModel):
    tank_id: int
    inspection_id: int | None = None

@router.post("/generate")
def generate_ppt(payload: GenerateRequest, db: Session = Depends(get_db), authorization: str = Header(None)):
    """
    Generates a PPT and saves it locally to /Backend/uploads/ppt
    Returns a JSON success message with the file path.
    """
    try:
        # --- DEBUG LOGGING ---
        print(f"DEBUG: Generating for Tank ID: {payload.tank_id}")
        # S3 migration: BASE_DIR and SAVE_DIRECTORY are not used

        # 1. Verify tank exists
        tank = db.query(Tank).filter(Tank.id == payload.tank_id).first()
        if not tank:
            raise HTTPException(status_code=404, detail=f"Tank with ID {payload.tank_id} not found")

        # 2. Get Report Number (Latest Inspection)
        report_number = "Unknown"
        try:
            # Using stored procedure for report number
            insp_sql = text("CALL sp_GetReportNumber(:tid, :iid)")
            params = {"tid": payload.tank_id, "iid": payload.inspection_id or 0}
            
            result = db.execute(insp_sql, params).first()
            if result and result[0]:
                report_number = result[0]
        except Exception as e:
            print(f"Warning: Could not fetch report number: {e}")

        # sanitize report number for filename usage
        report_number_safe = str(report_number).replace('/', '-').replace('\\', '-')
        tank_number_safe = str(tank.tank_number).replace('/', '-').replace('\\', '-')

        # 3. Generate the PPT (Returns BytesIO buffer)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ppt_buffer = create_presentation(db, payload.tank_id, base_dir, inspection_id=payload.inspection_id)
        
        # 4. Create logical filename
        # Requested format: "Tank Container Inspection Report - SMAU 8881402 - SG-T1-18122025-02.pptx"
        # Append timestamp to bypass caching
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        logical_name = f"Tank Container Inspection Report - {tank_number_safe} - {report_number_safe}_{timestamp_str}.pptx"

        # Build S3 key. We want to preserve Spaces and Case in the filename so the download looks good.
        # But we must ensure it's valid for S3/URL.
        now = datetime.utcnow()
        year = now.year
        month = f"{now.month:02d}"
        
        # Custom sanitize: Allow alphanumeric, spaces, dashes, underscores, dots, parenthesis.
        # Remove anything else to be safe.
        clean_name = re.sub(r'[^a-zA-Z0-9 \-_\.\(\)]', '', logical_name)
        
        # Ensure no leading/trailing dots/spaces
        clean_name = clean_name.strip().strip('.')

        s3_key = f"uploads/{PROJECT_NAME}/{year}/{month}/{clean_name}"
        # 5. Upload to S3
        ppt_buffer.seek(0)
        upload_fileobj_to_s3(ppt_buffer, s3_key, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        cdn_url = to_cdn_url(s3_key)
        # 6. Return JSON Success
        return JSONResponse(
            status_code=200,
            content={
                "message": "PPT generated and uploaded to S3 successfully.",
                "s3_key": s3_key,
                "cdn_url": cdn_url,
                "filename": logical_name
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like the 404 above) so they pass through
        raise
    except ValueError as e:
        # Catch value errors from the generator
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # CRITICAL: Print the real error to logs
        print("CRITICAL SERVER ERROR:")
        traceback.print_exc()
        # CRITICAL: Send the real error to Frontend for debugging
        raise HTTPException(status_code=500, detail=f"Debug Error: {str(e)}")

@router.get("/get-inspections/{tank_id}")
def get_tank_inspections(tank_id: int, db: Session = Depends(get_db)):
    """
    Get list of report numbers and inspection IDs for a tank where is_submitted=1 or web_submitted=1
    """
    try:
        # Using stored procedure for tank inspections
        sql = text("CALL sp_GetTankInspections(:tid)")
        results = db.execute(sql, {"tid": tank_id}).fetchall()
        
        return [
            {"report_number": row[0], "inspection_id": row[1]}
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))