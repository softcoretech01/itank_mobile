from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.tank_regulations import TankRegulation
from app.models.regulations_master import RegulationsMaster
from app.models.multiple_regulation import MultipleRegulation  # <-- add this import
from sqlalchemy import text
from app.routers.tank_inspection_router import get_current_user
router = APIRouter()

# -------- CREATE (Supports Multiple Selection) --------
@router.post("/")
def create_tank_regulation(
    payload: dict,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
    current_user = Depends(get_current_user)
):
    regulation_ids = payload.get("regulation_ids")
    if not regulation_ids:
        single = payload.get("regulation_id")
        if single:
            regulation_ids = [single]
    if not regulation_ids:
        raise HTTPException(400, "At least one regulation is required")

    tank_id = payload.get("tank_id")
    if not tank_id:
        raise HTTPException(400, "tank_id is required")

    regulation_ids = list(set(regulation_ids))  # remove duplicates

    # Get emp_id from the logged-in user
    if not current_user or not getattr(current_user, "emp_id", None):
        raise HTTPException(
            status_code=401,
            detail="Could not resolve emp_id from logged-in user"
        )
    emp_id = str(current_user.emp_id)

    # 1️⃣ Check if tank_regulation already exists
    tr = db.query(TankRegulation).filter(
        TankRegulation.tank_id == tank_id
    ).first()

    if not tr:
        # 2️⃣ Create ONE parent row
        tr = TankRegulation(
            tank_id=tank_id,
            initial_approval_no=payload.get("initial_approval_no"),
            imo_type=payload.get("imo_type"),
            safety_standard=payload.get("safety_standard"),
            country_registration=payload.get("country_registration"),
            created_by=emp_id,
        )
        db.add(tr)
        db.commit()
        db.refresh(tr)

    # 3️⃣ ALWAYS clear old children
    db.query(MultipleRegulation).filter(
        MultipleRegulation.reg_id == tr.id
    ).delete()

    # 4️⃣ Insert new children
    for rid in regulation_ids:
        rm = db.query(RegulationsMaster).filter_by(id=rid).first()
        if not rm:
            continue

        db.add(MultipleRegulation(
            reg_id=tr.id,
            regulation_id=rid,
            regulation_name=rm.regulation_name
        ))

    db.commit()

    # 5️⃣ Update count
    tr.count = len(regulation_ids)
    db.commit()

    return {
        "success": True,
        "message": "Tank regulation saved successfully",
        "tank_regulation_id": tr.id,
        "count": tr.count
    }

# =====================================================================
# 1) GET /regulation_master  -> all rows from RegulationsMaster
# =====================================================================
@router.get("/regulation_master")
def get_regulation_master(db: Session = Depends(get_db)):
    regs = db.query(RegulationsMaster).order_by(RegulationsMaster.id).all()
    return [
        {
            "id": r.id,
            "regulation_name": r.regulation_name,
            "created_by": getattr(r, "created_by", None),
            "updated_by": getattr(r, "updated_by", None),
            "created_at": getattr(r, "created_at", None),
            "updated_at": getattr(r, "updated_at", None),
        }
        for r in regs
    ]

# =====================================================================
# 2) GET /tank_regulation/{id}
#    -> one row from TankRegulation + all linked rows from MultipleRegulation
# =====================================================================
@router.get("/tank_regulation/{tank_reg_id}")
def get_tank_regulation(
    tank_reg_id: int,
    db: Session = Depends(get_db)
):
    """
    Input:
      tank_reg_id = TankRegulation.id (reg_id in multiple_regulation)

    Output:
      {
        "success": true/false,
        "message": "...",
        "data": {
          "tank_regulation": {...},
          "multiple_regulations": [...]
        }
      }
    """

    # 1) Main TankRegulation row
    tr = db.query(TankRegulation).filter(TankRegulation.id == tank_reg_id).first()
    if not tr:
        return {
            "success": False,
            "message": f"Tank regulation with id={tank_reg_id} not found",
            "data": {},
        }

    tank_regulation = {
        "id": tr.id,
        "tank_id": getattr(tr, "tank_id", None),
        "initial_approval_no": getattr(tr, "initial_approval_no", None),
        "imo_type": getattr(tr, "imo_type", None),
        "safety_standard": getattr(tr, "safety_standard", None),
        "country_registration": getattr(tr, "country_registration", None),
        "count": getattr(tr, "count", 0),
        "created_by": getattr(tr, "created_by", None),
        "updated_by": getattr(tr, "updated_by", None),
        "created_at": getattr(tr, "created_at", None),
        "updated_at": getattr(tr, "updated_at", None),
    }

    # 2) All linked rows from MultipleRegulation for this reg_id
    rows = (
        db.query(MultipleRegulation, RegulationsMaster)
        .outerjoin(
            RegulationsMaster,
            MultipleRegulation.regulation_id == RegulationsMaster.id,
        )
        .filter(MultipleRegulation.reg_id == tank_reg_id)
        .all()
    )

    multiple_regs = []
    for mr, rm in rows:
        multiple_regs.append(
            {
                "id": mr.id,
                "reg_id": mr.reg_id,                  # links back to tank_regulation.id
                "regulation_id": mr.regulation_id,
                "regulation": {
                    "id": mr.regulation_id,
                    "regulation_name": rm.regulation_name if rm else None,
                    "description": getattr(rm, "description", None) if rm else None,
                },
            }
        )

    return {
        "success": True,
        "message": "Tank regulation fetched successfully",
        "data": {
            "tank_regulation": tank_regulation,
            "multiple_regulations": multiple_regs,
        },
    }


# -----------------------------------------------------------------
# GET by tank_id -> return one row per selected regulation (MultipleRegulation)
# Endpoint used by frontend service: GET /tank-regulations/tank/{tankId}
# -----------------------------------------------------------------
@router.get("/tank/{tank_id}")
def get_by_tank_id(tank_id: int, db: Session = Depends(get_db)):
    tr = db.query(TankRegulation).filter(TankRegulation.tank_id == tank_id).first()
    if not tr:
        # Return empty array so frontend can handle 'no linked regs'
        return []

    # Fetch multiple_regulation rows for this tank_regulation
    rows = (
        db.query(MultipleRegulation)
        .filter(MultipleRegulation.reg_id == tr.id)
        .all()
    )

    out = []
    for mr in rows:
        out.append({
            "id": mr.id,
            "reg_id": mr.reg_id,
            "regulation_id": mr.regulation_id,
            "regulation_name": mr.regulation_name,
            "initial_approval_no": getattr(tr, "initial_approval_no", None),
            "imo_type": getattr(tr, "imo_type", None),
            "safety_standard": getattr(tr, "safety_standard", None),
            "country_registration": getattr(tr, "country_registration", None),
            "count": getattr(tr, "count", 0),
            "created_at": getattr(tr, "created_at", None),
        })

    return out

# =====================================================================
# 3) GET /multiple_regulation/{reg_id}
#    -> all rows from MultipleRegulation for that reg_id
# =====================================================================
@router.get("/multiple_regulation/{reg_id}")
def get_multiple_reg_by_reg_id(reg_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(MultipleRegulation, RegulationsMaster)
        .outerjoin(RegulationsMaster, MultipleRegulation.regulation_id == RegulationsMaster.id)
        .filter(MultipleRegulation.reg_id == reg_id)
        .all()
    )

    if not rows:
        # It's OK to return empty list, but if you want 404 instead, uncomment:
        # raise HTTPException(status_code=404, detail="No records for given reg_id")
        return []

    return [
        {
            "id": mr.id,
            "reg_id": mr.reg_id,
            "regulation_id": mr.regulation_id,
            "regulation_name": rm.regulation_name if rm else mr.regulation_name,
        }
        for mr, rm in rows
    ]

# -------- UPDATE --------
@router.put("/{reg_id}")
def update_tank_regulation(
    reg_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
    current_user = Depends(get_current_user)
):
    # 1) Fetch main tank_regulation row
    reg = db.query(TankRegulation).filter(TankRegulation.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Tank regulation not found")

    # Get emp_id from the logged-in user
    if not current_user or not getattr(current_user, "emp_id", None):
        raise HTTPException(
            status_code=401,
            detail="Could not resolve emp_id from logged-in user"
        )
    emp_id = str(current_user.emp_id)

    # 2) Clean payload ("" -> None)
    cleaned_payload: dict = {}
    for key, value in payload.items():
        cleaned_payload[key] = value if value != "" else None

    # 3) Pull out regulation_id(s) from payload – accept 'regulation_ids' (list) or 'regulation_id' (single)
    new_regulation_ids = None
    if "regulation_ids" in cleaned_payload:
        new_regulation_ids = cleaned_payload.pop("regulation_ids")
    else:
        new_regulation_ids = cleaned_payload.pop("regulation_id", None)

    # 4) Update TankRegulation columns (everything except regulation_id)
    for key, value in cleaned_payload.items():
        if hasattr(reg, key):
            setattr(reg, key, value)

    # Set updated_by
    reg.updated_by = emp_id

    # 5) Update multiple_regulation rows for this reg_id
    if new_regulation_ids is not None:
        # Normalize to a flat list of IDs
        if isinstance(new_regulation_ids, (list, tuple, set)):
            regs_list = [rid for rid in new_regulation_ids if rid is not None]
        else:
            regs_list = [new_regulation_ids] if new_regulation_ids is not None else []
        regs_list = list(set(regs_list))  # Remove duplicates

        # Validate IDs (if any)
        rm_by_id = {}
        if regs_list:
            rms = (
                db.query(RegulationsMaster)
                .filter(RegulationsMaster.id.in_(regs_list))
                .all()
            )
            rm_by_id = {rm.id: rm for rm in rms}
            invalid_ids = [rid for rid in regs_list if rid not in rm_by_id]
            if invalid_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid regulation_id(s): {invalid_ids}",
                )

        # Existing rows for this reg_id
        existing_rows = (
            db.query(MultipleRegulation)
            .filter(MultipleRegulation.reg_id == reg_id)
            .order_by(MultipleRegulation.id)
            .all()
        )

        # a) Update existing rows or create new ones to match regs_list
        for idx, rid in enumerate(regs_list):
            if idx < len(existing_rows):
                row = existing_rows[idx]
            else:
                row = MultipleRegulation(reg_id=reg_id)
                db.add(row)
                existing_rows.append(row)

            rm = rm_by_id.get(rid)
            row.regulation_id = rid
            row.regulation_name = rm.regulation_name if rm else None

        # b) Delete extra rows if regs_list is shorter than existing_rows
        if len(regs_list) < len(existing_rows):
            for row in existing_rows[len(regs_list):]:
                db.delete(row)

    db.commit()
    db.refresh(reg)

    # Update count
    reg.count = db.query(func.count(MultipleRegulation.id)).filter(MultipleRegulation.reg_id == reg.id).scalar()
    db.commit()

    return {
        "success": True,
        "message": "Tank regulation updated successfully",
        "data": {
            "tank_regulation": {
                "id": reg.id,
                "tank_id": getattr(reg, "tank_id", None),
                "initial_approval_no": getattr(reg, "initial_approval_no", None),
                "imo_type": getattr(reg, "imo_type", None),
                "safety_standard": getattr(reg, "safety_standard", None),
                "country_registration": getattr(reg, "country_registration", None),
                "count": getattr(reg, "count", 0),
                "created_by": getattr(reg, "created_by", None),
                "updated_by": getattr(reg, "updated_by", None),
                "created_at": getattr(reg, "created_at", None),
                "updated_at": getattr(reg, "updated_at", None),
            }
        },
    }



# -------- DELETE --------
@router.delete("/{reg_id}")
def delete_tank_regulation(reg_id: int, db: Session = Depends(get_db), authorization: str = Header(...)):
    # Try deleting a MultipleRegulation row first (child entry)
    mr = db.query(MultipleRegulation).filter(MultipleRegulation.id == reg_id).first()
    if mr:
        parent_id = mr.reg_id
        db.delete(mr)
        db.commit()
        # Update count
        parent = db.query(TankRegulation).filter(TankRegulation.id == parent_id).first()
        if parent:
            count = db.query(func.count(MultipleRegulation.id)).filter(MultipleRegulation.reg_id == parent_id).scalar()
            parent.count = count
            if count == 0:
                db.delete(parent)
            db.commit()
        return {"message": "Linked regulation removed successfully"}

    # Otherwise, attempt to delete a TankRegulation (parent) by id
    reg = db.query(TankRegulation).filter(TankRegulation.id == reg_id).first()
    if reg:
        # Delete all children first
        db.query(MultipleRegulation).filter(MultipleRegulation.reg_id == reg_id).delete()
        db.delete(reg)
        db.commit()
        return {"message": "Tank regulation deleted successfully"}

    raise HTTPException(status_code=404, detail="Record not found")
