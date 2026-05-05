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
    - tank_inspection_details: required fields are non-null
    - inspection_checklist: items for the inspection contain job_id/sub_job_id/sn/status_id
    - tank_images: at least 15 images uploaded
    """
    # 1) Check inspection row
    issues = {"inspection": [], "checklist": [], "to_do_list": [], "images": []}
    try:
        insp = db.execute(text("CALL sp_GetInspectionRow(:id)"), {"id": inspection_id}).mappings().first()
        if not insp:
            return _error(f"Inspection {inspection_id} not found", status_code=404)

        # Required fields to check (non-null and non-empty): This is a practical set
        required_inspection_fields = [
            "tank_id", "tank_number", "report_number", "inspection_date",
            "status_id", "product_id", "inspection_type_id", "location_id",
            "vacuum_reading", "lifter_weight_value",
        ]

        for f in required_inspection_fields:
            v = insp.get(f)
            if v is None or (isinstance(v, str) and v.strip() == ""):
                issues["inspection"].append({"field": f, "reason": "null or empty"})
            else:
                if isinstance(v, (int, float)) and int(v) == 0:
                    issues["inspection"].append({"field": f, "reason": "zero or invalid"})

    except Exception as e:
        logger.exception("Error validating inspection: %s", e)
        return _error(f"Error validating inspection: {e}", status_code=500)

    # validate PI next inspection date
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

    # 2) Validate inspection_checklist
    try:
        checklist_rows = db.execute(text("CALL sp_GetChecklistRows(:id)"), {"id": inspection_id}).mappings().fetchall() or []
        if not checklist_rows:
            issues["checklist"].append({"reason": "no checklist rows found for this inspection"})
        else:
            for rr in checklist_rows:
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
        todo_rows = db.execute(text("CALL sp_GetFlaggedTodoJobs(:id)"), {"id": inspection_id}).mappings().fetchall() or []
        
        if todo_rows:
            flagged_jobs = []
            for rr in todo_rows:
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

    # 3) Validate images
    try:
        img_rows = db.execute(
            text("SELECT image_type, image_path, thumbnail_path, image_id FROM tank_images WHERE inspection_id = :id"),
            {"id": inspection_id}
        ).mappings().fetchall() or []
        img_count = len(img_rows)

        db_types = db.execute(text("SELECT id, image_type, count FROM image_type")).mappings().fetchall() or []
        expected_by_id = {}
        for et in db_types:
            eid = et.get("id")
            cnt = et.get("count") or 1
            if eid is not None:
                expected_by_id[int(eid)] = int(cnt)

        from app.routers.tank_image_router import IMAGE_TYPES
        grouped = {}
        for info in IMAGE_TYPES.values():
            eid = int(info["image_type_id"])
            grouped.setdefault(eid, []).append(info)

        defs_by_id = {}
        expected_total_images = 0

        for eid in sorted(grouped.keys()):
            infos = grouped[eid]
            db_cnt = expected_by_id.get(eid)
            if db_cnt is None:
                db_cnt = max(1, len(infos))

            if eid == 4:
                slots = []
                for info in infos[:2]:
                    slots.append({"name": info["image_type"], "count": 1})
                    expected_total_images += 1
                defs_by_id[eid] = slots
                continue

            first_info = infos[0]
            cnt = int(db_cnt)
            defs_by_id[eid] = [{"name": first_info["image_type"], "count": cnt}]
            expected_total_images += cnt

        if expected_total_images == 0:
            expected_total_images = 15

        if img_count < expected_total_images:
            issues["images"].append({
                "reason": f"insufficient images: found {img_count}, expected {expected_total_images}"
            })

        for idx, rr in enumerate(img_rows):
            if not rr.get("image_path"):
                issues["images"].append({"index": idx + 1, "reason": "image_path missing"})
            if (not rr.get("image_id")) and (not rr.get("image_type")):
                issues["images"].append({"index": idx + 1, "reason": "image type missing"})

        actual_images_by_id = {}
        for rr in img_rows:
            rid = rr.get("image_id")
            if rid is None:
                continue
            try:
                rid_int = int(str(rid).strip())
            except Exception:
                continue
            actual_images_by_id.setdefault(rid_int, []).append(rr)

        missing_images = []
        for eid in sorted(defs_by_id.keys()):
            slot_defs = defs_by_id[eid]
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

    any_issues = any(len(v) > 0 for v in issues.values())
    if not any_issues:
        return _success({"inspection_id": inspection_id, "images_count": img_count, "checklist_count": len(checklist_rows)}, message="All validation checks passed")

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
