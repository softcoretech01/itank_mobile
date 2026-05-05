from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.utils import success_resp, error_resp 

router = APIRouter(prefix="/api/tank_checkpoints", tags=["Checkpoints"])

@router.get("/export/checklist")
def get_checklist_template(db: Session = Depends(get_db)):
    try:
        results = db.execute(text("CALL sp_GetChecklistTemplate()")).mappings().fetchall()

        sections_map = {}

        for r in results:
            # Now r['job_id'] works because of mappings()
            jid = str(r['job_id'])
            
            # 1. Create Section (With job_id included)
            if jid not in sections_map:
                sections_map[jid] = {
                    "sn": jid,               
                    "job_id": jid,           
                    "title": r['job_name'] or "", 
                    "items": []
                }
            
            # 2. Add Item (With job_id and sub_job_id included)
            if r['sub_job_id']:
                # Use the sn from database if available, otherwise generate it
                sn_val = r.get('sub_job_sn') or f"{jid}.{len(sections_map[jid]['items']) + 1}"
                
                sections_map[jid]["items"].append({
                    "sn": sn_val,
                    "title": r['sub_job_name'] or "",
                    "job_id": jid,                     
                    "sub_job_id": str(r['sub_job_id']) 
                })

        final_sections = list(sections_map.values())

        response_data = {
            "sections": final_sections
        }

        return success_resp("Checklist exported successfully", response_data, 200)

    except Exception as e:
        return error_resp(f"Error fetching checklist: {str(e)}", 500)