from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.cargo_tank import CargoTankTransaction
from app.database import get_db

router = APIRouter()

# ✅ CREATE
@router.post("/")
def create_transaction(request: dict, db: Session = Depends(get_db)):
    try:
        new_txn = CargoTankTransaction(
            tank_id=request["tank_id"],
            cargo_reference=request.get("cargo_master_id"),
            cargo_master_id=request.get("cargo_master_id"),
            density=request.get("density"),
            compatability_notes=request.get("compatability_notes"),
            loading_parts=request.get("loading_parts"),
            created_by=request.get("created_by"),
            updated_by=request.get("updated_by")
        )
        db.add(new_txn)
        db.commit()
        db.refresh(new_txn)
        return {"message": "Transaction created successfully", "data": new_txn}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ✅ GET ALL
@router.get("/")
def get_all_transactions(db: Session = Depends(get_db)):
    transactions = db.query(CargoTankTransaction).all()
    return {"count": len(transactions), "data": transactions}


# ✅ UPDATE
@router.put("/{transaction_id}")
def update_transaction(transaction_id: int, request: dict, db: Session = Depends(get_db)):
    txn = db.query(CargoTankTransaction).filter(CargoTankTransaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    for key, value in request.items():
        if hasattr(txn, key) and value is not None:
            setattr(txn, key, value)

    # Keep cargo_master_id and cargo_reference in sync if cargo_master_id provided
    if request.get("cargo_master_id") is not None:
        txn.cargo_master_id = request.get("cargo_master_id")
        if not txn.cargo_reference:
            txn.cargo_reference = request.get("cargo_master_id")

    db.commit()
    db.refresh(txn)
    return {"message": "Transaction updated successfully", "data": txn}


# ✅ GET BY TANK ID
@router.get("/tank/{tank_id}")
def get_transactions_by_tank(tank_id: int, db: Session = Depends(get_db)):
    from app.models.cargo_master import CargoTankMaster
    transactions = db.query(CargoTankTransaction, CargoTankMaster).join(
        CargoTankMaster, CargoTankTransaction.cargo_reference == CargoTankMaster.id
    ).filter(CargoTankTransaction.tank_id == tank_id).all()

    return [
        {
            "id": t[0].id,
            "tank_id": t[0].tank_id,
            "cargo_master_id": t[0].cargo_master_id or t[0].cargo_reference,
            "cargo_reference": t[1].cargo_reference,
            "density": t[0].density,
            "compatability_notes": t[0].compatability_notes,
            "loading_parts": t[0].loading_parts,
            "created_by": t[0].created_by,
            "updated_by": t[0].updated_by,
            "created_at": t[0].created_at,
            "updated_at": t[0].updated_at
        }
        for t in transactions
    ]

# ✅ DELETE
@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = db.query(CargoTankTransaction).filter(CargoTankTransaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(txn)
    db.commit()
    return {"message": "Transaction deleted successfully"}