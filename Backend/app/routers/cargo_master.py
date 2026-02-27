from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cargo_master import CargoTankMaster
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class CargoTankBase(BaseModel):
    cargo_reference: str
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class CargoTankCreate(CargoTankBase):
    pass

class CargoTankUpdate(BaseModel):
    cargo_reference: Optional[str] = None
    updated_by: Optional[str] = None

class CargoTankResponse(CargoTankBase):
    id: int
    class Config:
        from_attributes = True

@router.post("/", response_model=CargoTankResponse)
def create_cargo_tank(data: CargoTankCreate, db: Session = Depends(get_db)):
    new_record = CargoTankMaster(**data.dict())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@router.get("/", response_model=List[CargoTankResponse])
def get_all_cargo_tanks(db: Session = Depends(get_db)):
    records = db.query(CargoTankMaster).all()
    return records

@router.put("/{cargo_id}", response_model=CargoTankResponse)
def update_cargo_tank(cargo_id: int, data: CargoTankUpdate, db: Session = Depends(get_db)):
    record = db.query(CargoTankMaster).filter(CargoTankMaster.id == cargo_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record

@router.delete("/{cargo_id}")
def delete_cargo_tank(cargo_id: int, db: Session = Depends(get_db)):
    record = db.query(CargoTankMaster).filter(CargoTankMaster.id == cargo_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()
    return {"message": f"Cargo tank with id {cargo_id} deleted successfully"}
