from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.utils import success_resp, error_resp 

router = APIRouter(prefix="/api/tank_checkpoints", tags=["Checkpoints"])

@router.get("/export/checklist")
def get_checklist_template(db: Session = Depends(get_db)):
    try:
        # ---------------------------------------------------------
        # SQL: Select using actual DB column names with aliases
        # - inspection_job table uses 'id' as primary key (aliased as job_id)
        # - inspection_job table uses 'job_description' for title (aliased as job_name)
        # - inspection_sub_job table uses 'sub_job_id' as primary key
        # - inspection_sub_job table uses 'sub_job_description' for title (aliased as sub_job_name)
        # - inspection_sub_job table uses 'sn' for serial number
        # ---------------------------------------------------------
        query = """
            SELECT 
                j.id AS job_id, 
                j.job_description AS job_name, 
                j.sort_order AS job_sort_order,
                s.sub_job_id AS sub_job_id, 
                s.sub_job_name AS sub_job_name,
                s.sn AS sub_job_sn
            FROM inspection_job j
            LEFT JOIN inspection_sub_job s ON j.id = s.job_id
            ORDER BY j.sort_order ASC, s.sub_job_id ASC
        """
        
        results = db.execute(text(query)).fetchall()

        sections_map = {}

        for row in results:
            # Convert row to dictionary
            r = dict(row._mapping) if hasattr(row, "_mapping") else dict(zip(row.keys(), row))
            
            # Now r['job_id'] works because we aliased j.id as job_id
            jid = str(r['job_id'])
            
            # 1. Create Section (With job_id included)
            if jid not in sections_map:
                sections_map[jid] = {
                    "sn": jid,               
                    "job_id": jid,           
                    "title": r['job_name'] or "",  # Use job_name (aliased from job_description)
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