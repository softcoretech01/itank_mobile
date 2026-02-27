from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from app.database import get_db, get_db_connection
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.routers.tank_inspection_router import get_current_user
from app.routers.tank_image_router import IMAGE_TYPES
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validation", tags=["validation"])


def _error(message: str = "Error", status_code: int = 400):
    return JSONResponse(status_code=status_code, content={"success": False, "message": message, "data": {}})


def _success(data=None, message: str = "Operation successful"):
    return JSONResponse(status_code=200, content={"success": True, "message": message, "data": data or {}})


@router.get("/inspection/{inspection_id}")
def validate_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
):
    """
    Validate that for the given inspection_id:
    - tank_inspection_details: required fields are non-null (except operator_id, safety_valve_model_id, safety_valve_size_id allowed to be 0/null)
    - inspection_checklist: items for the inspection contain job_id/sub_job_id/sn/status_id
    - tank_images: at least 15 images uploaded; each image has image_path and image_type
    Returns lists of missing fields and any per-row issues found.
    """
    # 1) Check inspection row
    issues = {"inspection": [], "checklist": [], "to_do_list": [], "images": []}
    try:
        row = db.execute(text("SELECT * FROM tank_inspection_details WHERE inspection_id = :id LIMIT 1"), {"id": inspection_id}).fetchone()
        if not row:
            return _error(f"Inspection {inspection_id} not found", status_code=404)

        # convert to mapping/dict
        if hasattr(row, "_mapping"):
            insp = dict(row._mapping)
        elif isinstance(row, dict):
            insp = row
        else:
            try:
                insp = dict(zip(row.keys(), row))
            except Exception:
                insp = {}

        # Required fields to check (non-null and non-empty): This is a practical set
        required_inspection_fields = [
            "tank_id", "tank_number", "report_number", "inspection_date",
            "status_id", "product_id", "inspection_type_id", "location_id",
            "vacuum_reading", "lifter_weight_value",
            # pi_next_inspection_date will be validated separately (it can exist under several names)
        ]

        for f in required_inspection_fields:
            v = insp.get(f)
            if v is None or (isinstance(v, str) and v.strip() == ""):
                issues["inspection"].append({"field": f, "reason": "null or empty"})
            else:
                # If numeric check: value shouldn't be 0 (except allowed columns)
                if isinstance(v, (int, float)) and int(v) == 0:
                    issues["inspection"].append({"field": f, "reason": "zero or invalid"})

        # operator_id, safety_valve_model_id and safety_valve_size_id are allowed to be 0
        # Other fields like lifter_weight etc. are optional; we do not enforce them here

    except Exception as e:
        logger.exception("Error validating inspection: %s", e)
        return _error(f"Error validating inspection: {e}", status_code=500)

    # validate PI next inspection date (several column name variants may exist)
    try:
        pi_keys = ["pi_next_inspection_date", "pi_next_insp_date", "next_insp_date", "pi_nextinsp_date"]
        pi_found = False
        for k in pi_keys:
            v = insp.get(k)
            if v is not None and not (isinstance(v, str) and v.strip() == ""):
                pi_found = True
                break
        if not pi_found:
            issues["inspection"].append({"field": "pi_next_inspection_date", "reason": "null or empty (or alternate name missing)"})
    except Exception:
        pass

    # 2) Validate inspection_checklist (items exist and fields present)
    try:
        checklist_rows = db.execute(text("SELECT * FROM inspection_checklist WHERE inspection_id = :id"), {"id": inspection_id}).fetchall() or []
        if not checklist_rows:
            issues["checklist"].append({"reason": "no checklist rows found for this inspection"})
        else:
            for r in checklist_rows:
                rr = dict(r._mapping) if hasattr(r, "_mapping") else dict(zip(r.keys(), r))
                row_issue = {"id": rr.get("id")}
                for f in ("job_id", "sub_job_id", "sn", "status_id"):
                    v = rr.get(f)
                    if v is None or (isinstance(v, str) and v.strip() == ""):
                        row_issue.setdefault("missing_fields", []).append(f)
                if "missing_fields" in row_issue:
                    issues["checklist"].append(row_issue)
    except Exception as e:
        logger.exception("Error validating checklist for inspection %s: %s", inspection_id, e)
        return _error(f"Error validating checklist: {e}", status_code=500)

    # 2.5) Validate to_do_list is empty for this inspection
    try:
        todo_rows = db.execute(text("""
            SELECT DISTINCT c.job_id, c.job_name, t.status_id
            FROM to_do_list t
            LEFT JOIN inspection_checklist c ON t.checklist_id = c.id
            WHERE t.inspection_id = :id AND t.status_id = 2
            ORDER BY c.job_id
        """), {"id": inspection_id}).fetchall() or []
        
        if todo_rows:
            flagged_jobs = []
            for r in todo_rows:
                rr = dict(r._mapping) if hasattr(r, "_mapping") else dict(zip(r.keys(), r))
                job_id = rr.get("job_id")
                job_name = rr.get("job_name")
                if job_id is not None:
                    flagged_jobs.append({
                        "job_id": str(job_id),
                        "job_name": job_name or "",
                        "status_id": 2
                    })
            
            if flagged_jobs:
                issues["to_do_list"] = [{
                    "reason": "to_do_list not empty - inspection has flagged items",
                    "flagged_jobs": flagged_jobs
                }]
    except Exception as e:
        logger.exception("Error validating to_do_list for inspection %s: %s", inspection_id, e)
        # Don't fail the whole validation, just log the error

    # Helper: normalize names (strip non-alpha, lower)
    def _norm_name(s):
        if s is None:
            return None
        try:
            s2 = str(s).strip().lower()
        except Exception:
            s2 = str(s)
        # Keep only letters a-z to normalize common variants e.g. 'Underside View 01' -> 'undersideview'
        return re.sub('[^a-z]', '', s2)
           # 3) Validate images: counts and missing types
    # 3) Validate images: check count >= expected and expected image counts per type
    try:
        img_rows = db.execute(
            text("SELECT image_type, image_path, thumbnail_path, image_id FROM tank_images WHERE inspection_id = :id"),
            {"id": inspection_id}
        ).fetchall() or []
        img_count = len(img_rows)

        # Load counts from DB image_type table
        db_types = db.execute(
            text("SELECT id, image_type, count FROM image_type")
        ).fetchall() or []
        expected_by_id = {}
        for et in db_types:
            if hasattr(et, "_mapping"):
                eid = et._mapping.get("id")
                cnt = et._mapping.get("count") or 1
            elif isinstance(et, dict):
                eid = et.get("id")
                cnt = et.get("count") or 1
            else:
                try:
                    eid, _, cnt = et
                except Exception:
                    continue
            if eid is not None:
                expected_by_id[int(eid)] = int(cnt)

        # ---- NEW: drive expectations from IMAGE_TYPES so underside 01/02 are separate ----
        # ---- Drive expectations from IMAGE_TYPES, but split underside views as two slots ----
        from app.routers.tank_image_router import IMAGE_TYPES

        # Group IMAGE_TYPES entries by image_type_id
        grouped = {}
        for info in IMAGE_TYPES.values():
            eid = int(info["image_type_id"])
            grouped.setdefault(eid, []).append(info)

        # defs_by_id: image_type_id -> list of logical slots
        # each slot = {"name": <display_name>, "count": <expected_count_for_this_slot>}
        defs_by_id = {}
        expected_total_images = 0

        for eid in sorted(grouped.keys()):
            infos = grouped[eid]

            # total count configured in DB for this id (if any)
            db_cnt = expected_by_id.get(eid)
            if db_cnt is None:
                db_cnt = max(1, len(infos))

            # SPECIAL CASE: underside (id = 4)
            # We want two slots:
            #   - "Underside View 01" index 1
            #   - "Underside View 02" index 2
            # each with count = 1, regardless of db_cnt (which should be 2).
            if eid == 4:
                slots = []
                for info in infos[:2]:  # use first two IMAGE_TYPES entries
                    slots.append({"name": info["image_type"], "count": 1})
                    expected_total_images += 1
                defs_by_id[eid] = slots
                continue

            # All other ids: single logical slot with count from DB
            first_info = infos[0]
            cnt = int(db_cnt)
            defs_by_id[eid] = [{"name": first_info["image_type"], "count": cnt}]
            expected_total_images += cnt

        # If there is somehow no config, fall back to 15
        if expected_total_images == 0:
            expected_total_images = 15

        # basic count check
        if img_count < expected_total_images:
            issues["images"].append({
                "reason": f"insufficient images: found {img_count}, expected {expected_total_images}"
            })

        # Check each image row has required fields
        for idx, r in enumerate(img_rows):
            rr = dict(r._mapping) if hasattr(r, "_mapping") else dict(zip(r.keys(), r))
            if not rr.get("image_path"):
                issues["images"].append({"index": idx + 1, "reason": "image_path missing"})
            if (not rr.get("image_id")) and (not rr.get("image_type")):
                issues["images"].append({"index": idx + 1, "reason": "image type missing"})

        # Build map of actual images by image_type_id (image_id column)
        actual_images_by_id = {}
        for r in img_rows:
            rr = dict(r._mapping) if hasattr(r, "_mapping") else dict(zip(r.keys(), r))
            rid = rr.get("image_id")
            if rid is None:
                continue
            try:
                rid_int = int(str(rid).strip())
            except Exception:
                continue
            actual_images_by_id.setdefault(rid_int, []).append(rr)

        # For each image_type_id, decide which logical slots are missing
        missing_images = []
        for eid in sorted(defs_by_id.keys()):
            slot_defs = defs_by_id[eid]              # list of {"name", "count"}
            actual_ct = len(actual_images_by_id.get(eid, []))
            total_expected_for_id = sum(d["count"] for d in slot_defs)
            total_missing_for_id = total_expected_for_id - actual_ct
            if total_missing_for_id <= 0:
                continue

            next_index = actual_ct + 1
            for slot in slot_defs:
                slot_name = slot["name"]
                slot_expected = slot["count"]
                for _ in range(slot_expected):
                    if total_missing_for_id <= 0:
                        break
                    missing_images.append({
                        "image_type_id": eid,
                        "image_type": slot_name,
                        "reason": "missing image",
                        "index": next_index,
                    })
                    next_index += 1
                    total_missing_for_id -= 1
                if total_missing_for_id <= 0:
                    break

        if missing_images:
            issues["images"].append({"reason": "missing images", "missing": missing_images})


    except Exception as e:
        logger.exception("Error validating images for inspection %s: %s", inspection_id, e)
        return _error(f"Error validating images: {e}", status_code=500)



    # If there are no issues, success
    any_issues = any(len(v) > 0 for v in issues.values())
    if not any_issues:
        # return a simple success and counts
        return _success({"inspection_id": inspection_id, "images_count": img_count, "checklist_count": len(checklist_rows)}, message="All validation checks passed")

    # Return error if issues found
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "Validation issues found",
            "data": {
                "inspection_id": inspection_id,
                "issues": issues
            }
        }
    )
