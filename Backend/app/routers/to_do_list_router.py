from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Any
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.database import get_db_connection, get_db

# Local response helpers to avoid circular imports
from fastapi.encoders import jsonable_encoder
def success_resp(message: str, data: Any = None, status_code: int = 200):
    if data is None:
        data = {}
    try:
        payload = jsonable_encoder(data)
    except Exception:
        try:
            payload = jsonable_encoder(str(data))
        except Exception:
            payload = {}
    return JSONResponse(status_code=status_code, content={"success": True, "message": message, "data": payload})

def error_resp(message: str, status_code: int = 400):
    return JSONResponse(status_code=status_code, content={"success": False, "message": message, "data": {}})
from app.models.to_do_list_model import ToDoList
from pymysql.cursors import DictCursor
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/to_do_list", tags=["to_do_list"])


def _normalize_int(v, default=None):
    if v is None:
        return default
    try:
        if isinstance(v, int):
            return v
        vs = str(v).strip()
        if vs == "":
            return default
        return int(vs)
    except Exception:
        return default


# ----------------------------
# RESPONSE MODELS
class ToDoListResponse(BaseModel):
    id: int
    checklist_id: int
    inspection_id: int
    tank_id: Optional[int]
    job_name: Optional[str]
    sub_job_description: Optional[str]
    sn: str
    status_name: Optional[str]
    comment: Optional[str]
    created_at: str

class ToDoBulkItem(BaseModel):
    id: int             # To-Do ID
    status_id: int
    comment: Optional[str] = None


class GenericResponse(BaseModel):
    success: bool
    data: List[dict]



# ----------------------------
# HELPER: SYNC FLAGGED ITEMS
# ----------------------------
def _sync_flagged_to_todo(cursor, checklist_id: int):
    """
    Sync a flagged checklist row to to_do_list.
    Now uses inspection_id instead of report_id.
    """
    cursor.execute("""
        SELECT id, inspection_id, tank_id, job_name, sub_job_description, sn, status_id, comment, created_at
        FROM inspection_checklist
        WHERE id=%s AND flagged=1
    """, (checklist_id,))
    row = cursor.fetchone()
    if not row:
        return
    cursor.execute("""
        INSERT INTO to_do_list (checklist_id, inspection_id, tank_id, job_name, sub_job_description, sn, status_id, comment, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            inspection_id=VALUES(inspection_id),
            tank_id=VALUES(tank_id),
            job_name=VALUES(job_name),
            sub_job_description=VALUES(sub_job_description),
            status_id=VALUES(status_id),
            comment=VALUES(comment)
    """, (
        checklist_id,
        row['inspection_id'],
            row['tank_id'],
        row['job_name'],
        row['sub_job_description'],
        row['sn'],
        row['status_id'],
        row['comment'],
        row['created_at']
    ))


# ----------------------------
# GET ALL TO-DO ITEMS
# ----------------------------
@router.get("/list", response_model=GenericResponse)
def get_to_do_list():
    conn = get_db_connection()
    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute("""
                SELECT id, checklist_id, inspection_id, tank_id, job_name, sub_job_description,
                       sn, status_id, comment, created_at
                FROM to_do_list
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall() or []

            # Convert numeric status_id -> status_name
            # Build inspection_status map (best effort, fallback to empty string)
            status_map = {}
            try:
                cursor.execute("SELECT status_id, status_name FROM inspection_status")
                for r in cursor.fetchall() or []:
                    status_map[r.get('status_id')] = r.get('status_name')
            except Exception:
                status_map = {}

            # Build checklist_id -> (job_id, sub_job_id) map to get numeric job ids where possible
            checklist_ids = [r.get('checklist_id') for r in rows if r.get('checklist_id')]
            checklist_map = {}
            if checklist_ids:
                try:
                    fmt = ','.join(['%s'] * len(checklist_ids))
                    cursor.execute(f"SELECT id, job_id, sub_job_id FROM inspection_checklist WHERE id IN ({fmt})", tuple(checklist_ids))
                    for cr in cursor.fetchall() or []:
                        checklist_map[cr.get('id')] = cr
                except Exception:
                    checklist_map = {}

            # Group rows into job groups
            from collections import OrderedDict, Counter
            groups = OrderedDict()
            for r in rows:
                chk_id = r.get('checklist_id')
                job_id = None
                sub_id = None
                if chk_id and chk_id in checklist_map:
                    job_id = checklist_map[chk_id].get('job_id')
                    sub_id = checklist_map[chk_id].get('sub_job_id')

                # prefer numeric job_id where available, else use job_name as key
                if job_id is not None and str(job_id).isdigit():
                    job_key = int(job_id)
                    job_id_out = str(int(job_id))
                else:
                    job_key = r.get('job_name') or "Other"
                    job_id_out = None

                title = r.get('job_name') or "Other"

                if job_key not in groups:
                    groups[job_key] = {"job_id": job_id_out, "title": title, "status_ids": [], "items": [], "_seen": set()}

                # dedupe by (sub_job_id, sn)
                sn_val = r.get('sn') or ""
                dedupe_key = (None if sub_id is None else (int(sub_id) if str(sub_id).isdigit() else str(sub_id)), str(sn_val))
                if dedupe_key in groups[job_key]["_seen"]:
                    # collect status_id for later aggregation
                    sid_value = r.get('status_id')
                    if sid_value is not None:
                        groups[job_key]["status_ids"].append(sid_value)
                    continue

                groups[job_key]["_seen"].add(dedupe_key)
                sid_value = r.get('status_id')
                if sid_value is not None:
                    groups[job_key]["status_ids"].append(sid_value)

                groups[job_key]["items"].append({
                    "sn": sn_val,
                    "title": r.get('sub_job_description') or "",
                    "comment": r.get('comment') or "",
                    "sub_job_id": sub_id if sub_id is not None else None
                })

            # finalize groups -> list, choose most common status_name per group (or blank)
            out = []
            for k in groups.keys():
                grp = groups[k]
                status_id_out = ""
                if grp["status_ids"]:
                    cnt = Counter([s for s in grp["status_ids"] if s is not None])
                    if cnt:
                        most_common = cnt.most_common(1)[0][0]
                        status_id_out = str(most_common) if most_common is not None else ""
                out.append({
                    "job_id": grp["job_id"],
                    "title": grp["title"],
                    "status_id": status_id_out or "",
                    "items": grp["items"]
                })

            return success_resp("To-do list fetched", out, 200)
    finally:
        conn.close()


# ----------------------------
# DELETE TO-DO ITEM
# ----------------------------
@router.delete("/delete/{to_do_id}")
def delete_to_do_item(to_do_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute("SELECT 1 FROM to_do_list WHERE id=%s", (to_do_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"To-do item {to_do_id} not found")
            
            cursor.execute("DELETE FROM to_do_list WHERE id=%s", (to_do_id,))
            conn.commit()
            return success_resp("To-do item deleted", {"id": to_do_id}, 200)
    finally:
        conn.close()



@router.get("/flagged/inspection/{inspection_id}/grouped")
@router.get("/flagged/inspection/{inspection_id}/grouped/")
def get_flagged_by_inspection_grouped(inspection_id: int):
    """
    Return flagged items for an inspection grouped into sections.
    Uses SQL JOINs to ensure job_id and sub_job_id are retrieved correctly.
    Normalizes numeric fields to integers where possible.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(DictCursor) as cursor:
            # 1. Fetch To-Do Items with JOIN to get checklist details (job_id, sub_job_id)
            query = """
                SELECT 
                    t.sn, 
                    t.sub_job_description as title,
                    t.status_id,
                    t.checklist_id,
                    t.tank_id,
                    t.job_name,
                    c.job_id, 
                    c.sub_job_id, 
                    c.emp_id as checklist_emp_id,
                    t.comment
                FROM to_do_list t
                LEFT JOIN inspection_checklist c ON t.checklist_id = c.id
                WHERE t.inspection_id = %s
                ORDER BY t.created_at DESC
            """
            cursor.execute(query, (inspection_id,))
            rows = cursor.fetchall() or []

            # 2. Get Header Info (Fallback for emp_id)
            cursor.execute("SELECT emp_id, tank_id FROM tank_inspection_details WHERE inspection_id=%s LIMIT 1", (inspection_id,))
            header = cursor.fetchone()

            header_emp_id = _normalize_int(header.get("emp_id")) if header and header.get("emp_id") is not None else None
            header_tank_id = _normalize_int(header.get("tank_id")) if header and header.get("tank_id") is not None else None

            # 3. Group the items
            sections = {}
            # Deduplication set: (job_id, sub_job_id, sn)
            seen_items = set()
            for r in rows:
                job_id = r.get('job_id')
                sub_id = r.get('sub_job_id')
                sn_val = r.get('sn') or ""
                job_key = str(job_id) if job_id is not None else ""
                sub_key = str(sub_id) if sub_id is not None else ""
                section_title = r.get('job_name') or "Unknown Section"

                # Initialize section if not exists
                if job_key not in sections:
                    sections[job_key] = {
                        "job_id": job_key,
                        "title": section_title,
                        "items": [],
                        "status_ids": []
                    }

                # Deduplicate by (job_id, sub_job_id, sn)
                dedupe_key = (job_key, sub_key, sn_val)
                if dedupe_key in seen_items:
                    # collect status for aggregation
                    if r.get('status_id') is not None:
                        sections[job_key]["status_ids"].append(r.get('status_id'))
                    continue
                seen_items.add(dedupe_key)

                # collect status_id for aggregation
                if r.get('status_id') is not None:
                    sections[job_key]["status_ids"].append(r.get('status_id'))

                sections[job_key]["items"].append({
                    "sn": sn_val,
                    "title": r.get('title'),
                    "job_id": job_key,
                    "sub_job_id": _normalize_int(sub_id),
                    "status_id": _normalize_int(r.get('status_id')),
                    "comment": r.get('comment') or "",
                })

            # 4. Final Response Construction
            # Use header emp_id if we have it, otherwise try to find one from the rows
            final_emp_id = header_emp_id
            if final_emp_id is None and rows:
                if rows[0].get('checklist_emp_id'):
                    final_emp_id = _normalize_int(rows[0].get('checklist_emp_id'))

            # Build output sections list with normalized job_id and aggregated status_id
            from collections import Counter
            out_sections = []
            for job_key, grp in sections.items():
                status_id_out = None
                if grp.get("status_ids"):
                    cnt = Counter([s for s in grp.get("status_ids") if s is not None])
                    if cnt:
                        most_common = cnt.most_common(1)[0][0]
                        status_id_out = _normalize_int(most_common)

                job_id_out = _normalize_int(job_key) if job_key is not None and str(job_key).isdigit() else (job_key if job_key != "" else None)

                out_sections.append({
                    "job_id": job_id_out,
                    "title": grp.get("title"),
                    "status_id": status_id_out,
                    "items": grp.get("items", [])
                })

            resp = {
                "inspection_id": _normalize_int(inspection_id),
                "tank_id": header_tank_id if header_tank_id is not None else (_normalize_int(rows[0].get('tank_id')) if rows and rows[0].get('tank_id') is not None else None),
                "emp_id": final_emp_id,
                "sections": out_sections,
            }
            return success_resp("Flagged items fetched (grouped)", resp, 200)

    except Exception as e:
        logger.error(f"Error fetching grouped flagged items for inspection {inspection_id}: {e}", exc_info=True)
        return error_resp(str(e), 500)
    finally:
        conn.close()

# ----------------------------
# UPDATE TO-DO ITEM (SYNC BACK)
# ----------------------------
from fastapi import Header
from typing import Union

class ToDoJobUpdate(BaseModel):
    job_id: Union[int, str]
    status_id: int
    comment: Optional[str] = None


class ToDoSubJobItem(BaseModel):
    sub_job_id: Optional[Union[int, str]] = None
    sn: Optional[str] = None
    title: Optional[str] = None
    comment: Optional[str] = None
    job_id: Optional[Union[int, str]] = None
    status_id: Optional[Union[int, str]] = None


class ToDoSection(BaseModel):
    sn: Optional[str] = None
    job_id: Optional[Union[int, str]] = None
    title: Optional[str] = None
    status_id: Optional[Union[int, str]] = None
    items: List[ToDoSubJobItem]


class ToDoUpdatePayload(BaseModel):
    inspection_id: Union[int, str]
    tank_id: Optional[Union[int, str]] = None
    sections: List[ToDoSection]
    
    class Config:
        json_schema_extra = {
            "example": {
                "inspection_id": 123,
                "sections": [
                    {
                        "sn": "1",
                        "job_id": "1",
                        "title": "Tank Body & Frame Condition",                       
                        "items": [
                            {"sn": "1.1", "title": "Body x 6 Sides & All Frame – No Dent / No Bent / No Deep Cut", "sub_job_id": "1", "job_id": "1", "status_id":"","comment": ""},
                            {"sn": "1.2", "title": "Cabin Door & Frame Condition – No Damage / Can Lock", "sub_job_id": "2", "job_id": "1", "status_id":"","comment": ""},
                            {"sn": "1.3", "title": "Tank Number, Product & Hazchem Label – Not Missing or Tear", "sub_job_id": "3", "job_id": "1","status_id":"", "comment": ""},
                            {"sn": "1.4", "title": "Condition of Paint Work & Cleanliness – Clean / No Bad Rust", "sub_job_id": "4", "job_id": "1","status_id":"", "comment": ""},
                            {"sn": "1.5", "title": "Others", "sub_job_id": "5", "job_id": "1","status_id":"", "comment": ""}
                        ]
                    },
                    {
                        "sn": "2",
                        "job_id": "2",
                        "title": "Pipework & Installation",
                        "items": [
                            {"sn": "2.1", "title": "Pipework Supports / Brackets – Not Loose / No Bent", "sub_job_id": "6", "job_id": "2","status_id":"", "comment": ""},
                            {"sn": "2.2", "title": "Pipework Joint & Welding – No Crack / No Icing / No Leaking", "sub_job_id": "7", "job_id": "2", "status_id":"","comment": ""},
                            {"sn": "2.3", "title": "Earthing Point", "sub_job_id": "8", "job_id": "2", "status_id":"","comment": ""},
                            {"sn": "2.4", "title": "PBU Support & Flange Connection – No Leak / Not Damage", "sub_job_id": "9", "job_id": "2","status_id":"", "comment": ""},
                            {"sn": "2.5", "title": "Others", "sub_job_id": "10", "job_id": "2", "status_id":"","comment": ""}
                        ]
                    },
                    {
                        "sn": "3",
                        "job_id": "3",
                        "title": "Tank Instrument & Assembly",
                        "items": [
                            {"sn": "3.1", "title": "Safety Diverter Valve – Switching Lever", "sub_job_id": "11", "job_id": "3","status_id":"", "comment": ""},
                            {"sn": "3.2", "title": "Safety Valves Connection & Joint – No Leaks", "sub_job_id": "12", "job_id": "3", "status_id":"","comment": ""},
                            {"sn": "3.3", "title": "Level & Pressure Gauge Support Bracket, Connection & Joint – Not Loosen / No Leaks", "sub_job_id": "13", "job_id": "3", "status_id":"","comment": ""},
                            {"sn": "3.4", "title": "Level & Pressure Gauge – Function Check", "sub_job_id": "14", "job_id": "3", "status_id":"","comment": ""},
                            {"sn": "3.5", "title": "Level & Pressure Gauge Valve Open / Balance Valve Close", "sub_job_id": "15", "job_id": "3", "status_id":"","comment": ""},
                            {"sn": "3.6", "title": "Data & CSC Plate – Not Missing / Not Damage", "sub_job_id": "16", "job_id": "3", 	"status_id":"","comment": ""},
                            {"sn": "3.7", "title": "Others", "sub_job_id": "17", "job_id": "3", "status_id":"","comment": ""}
                        ]
                    },
                    {
                        "sn": "4",
                        "job_id": "4",
                        "title": "Valves Tightness & Operation",
                        "items": [
                            {"sn": "4.1", "title": "Valve Handwheel – Not Missing / Nut Not Loose", "sub_job_id": "18", "job_id": "4", "status_id":"", "comment": ""},
                            {"sn": "4.2", "title": "Valve Open & Close Operation – No Seizing / Not Tight / Not Jam", "sub_job_id": "19", "job_id": "4","status_id":"", "comment": ""},
                            {"sn": "4.3", "title": "Valve Tightness Incl Glands – No Leak / No Icing / No Passing", "sub_job_id": "20", "job_id": "4", "status_id":"","comment": ""},
                            {"sn": "4.4", "title": "Anchor Point", "sub_job_id": "21", "job_id": "4", "status_id":"","comment": ""},
                            {"sn": "4.5", "title": "Others", "sub_job_id": "22", "job_id": "4", "status_id":"","comment": ""}
                        ]
                    },
                    {
                        "sn": "5",
                        "job_id": "5",
                        "title": "Before Departure Check",
                        "items": [
                            {"sn": "5.1", "title": "All Valves Closed – Defrost & Close Firmly", "sub_job_id": "23", "job_id": "5", "status_id":"","comment": ""},
                            {"sn": "5.2", "title": "Caps fitted to Outlets or Cover from Dust if applicable", "sub_job_id": "24", "job_id": "5", "status_id":"","comment": ""},
                            {"sn": "5.3", "title": "Security Seal Fitted by Refilling Plant - Check", "sub_job_id": "25", "job_id": "5", "status_id":"","comment": ""},
                            {"sn": "5.4", "title": "Pressure Gauge – lowest possible", "sub_job_id": "26", "job_id": "5", "status_id":"","comment": ""},
                            {"sn": "5.5", "title": "Level Gauge – Within marking or standard indication", "sub_job_id": "27", "job_id": "5", "status_id":"","comment": ""},
                            {"sn": "5.6", "title": "Weight Reading – ensure within acceptance weight", "sub_job_id": "28", "job_id": "5", "status_id":"","comment": ""},
                            {"sn": "5.7", "title": "Cabin Door Lock – Secure and prevent from sudden opening", "sub_job_id": "29", "job_id": "5", 	"status_id":"","comment": ""},
                            {"sn": "5.8", "title": "Others", "sub_job_id": "30", "job_id": "5", "status_id":"","comment": ""}
                        ]
                    },
                    {
                        "sn": "6",
                        "job_id": "6",
                        "title": "Others Observation & Comment",
                        "items": [{"sn": "6.1", "title": "Others Observation & GeneralComment", "comment": "", "sub_job_id": "31","status_id": ""}]
                    }
                ]
            }
        }


@router.put("/update")
def update_to_do_by_inspection(
    payload: ToDoUpdatePayload,
    Authorization: Optional[str] = Header(None),
):
    """
    Update To-Do items by inspection_id.
    Accepts the same payload structure as checklist endpoints.
    
    - Updates status_id for sections where provided (non-empty)
    - If status_id changes from 2 to 1 or 3, removes items from to_do_list
    - Updates ALL inspection_checklist rows for that job_id
    - Updates comments if provided
    
    Authorization header is required.
    inspection_id is required in the request body.
    """
    if not Authorization:
        return error_resp("Authorization required", 401)
    
    inspection_id = payload.inspection_id
    if inspection_id is None or str(inspection_id).strip() == "":
        return error_resp("inspection_id required in body", 400)
    
    try:
        inspection_id = int(str(inspection_id))
    except Exception:
        return error_resp("Invalid inspection_id value", 400)
    
    conn = get_db_connection()
    try:
        with conn.cursor(DictCursor) as cursor:
            updated_items = []
            
            for section in payload.sections:
                job_id = getattr(section, 'job_id', None)
                if job_id is None or str(job_id).strip() == "":
                    continue
                try:
                    job_id = int(str(job_id))
                except ValueError:
                    continue
                
                for item in section.items:
                    item_status_id = getattr(item, 'status_id', None)
                    if item_status_id is None or str(item_status_id).strip() == "":
                        continue
                    
                    try:
                        new_status_id = int(str(item_status_id))
                    except ValueError:
                        continue
                    
                    sub_job_id = getattr(item, 'sub_job_id', None)
                    if sub_job_id is None or str(sub_job_id).strip() == "":
                        continue
                    try:
                        sub_job_id = int(str(sub_job_id))
                    except ValueError:
                        continue
                    
                    item_comment = getattr(item, 'comment', None)
                    
                    # Fetch and update status name
                    status_name = None
                    try:
                        cursor.execute(
                            "SELECT status_name FROM inspection_status WHERE status_id = %s LIMIT 1",
                            (new_status_id,),
                        )
                        status_row = cursor.fetchone()
                        if status_row:
                            status_name = status_row.get("status_name")
                    except Exception:
                        pass
                    
                    # Determine if this status should be flagged (only status_id=2 is flagged)
                    new_flagged = 1 if new_status_id == 2 else 0
                    
                    # Update the specific sub_job
                    update_sql = """
                        UPDATE inspection_checklist 
                        SET status_id=%s, flagged=%s, updated_at=NOW()
                    """
                    update_params = [new_status_id, new_flagged]
                    
                    if status_name:
                        update_sql += ", status=%s"
                        update_params.append(status_name)
                    
                    if item_comment is not None:
                        update_sql += ", comment=%s"
                        update_params.append(item_comment)
                    
                    update_sql += " WHERE inspection_id=%s AND job_id=%s AND sub_job_id=%s"
                    update_params.extend([inspection_id, job_id, sub_job_id])
                    
                    cursor.execute(update_sql, tuple(update_params))
                    
                    # Handle to_do_list
                    # Find the checklist_id for this sub_job
                    cursor.execute("""
                        SELECT id FROM inspection_checklist 
                        WHERE inspection_id=%s AND job_id=%s AND sub_job_id=%s LIMIT 1
                    """, (inspection_id, job_id, sub_job_id))
                    checklist_row = cursor.fetchone()
                    if checklist_row:
                        checklist_id = checklist_row['id']
                        
                        if new_status_id == 2:
                            # Add or update in to_do_list
                            cursor.execute("""
                                INSERT INTO to_do_list (checklist_id, inspection_id, tank_id, job_name, sub_job_description, sn, status_id, comment, created_at)
                                SELECT id, inspection_id, tank_id, job_name, sub_job_description, sn, status_id, comment, created_at
                                FROM inspection_checklist WHERE id=%s
                                ON DUPLICATE KEY UPDATE
                                    status_id=VALUES(status_id),
                                    comment=VALUES(comment)
                            """, (checklist_id,))
                        else:
                            # Remove from to_do_list if status changed from 2
                            cursor.execute("DELETE FROM to_do_list WHERE checklist_id=%s", (checklist_id,))
                    
                    updated_items.append({
                        "job_id": str(job_id),
                        "sub_job_id": str(sub_job_id),
                        "status_id": str(new_status_id),
                        "comment": item_comment or ""
                    })
            
            conn.commit()
            return success_resp(f"Successfully updated {len(updated_items)} item(s)", {
                "inspection_id": str(inspection_id),
                "tank_id": str(payload.tank_id),
                "updated_items": updated_items
            }, 200)
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating to-do by inspection: {e}", exc_info=True)
        return error_resp(str(e), 500)
    finally:
        conn.close()
