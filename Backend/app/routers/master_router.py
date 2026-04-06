from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
# Import your models (ensure these paths match your project)
from app.models.manufacturer_master_model import ManufacturerMaster
from app.models.standard_master_model import StandardMaster
from app.models.tankcode_iso_master_model import TankCodeISOMaster
from app.models.un_code_master_model import UNISOCODEMaster
from app.models.design_temperature_master_model import DesignTemperatureMaster
from app.models.cabinet_type_master_model import CabinetTypeMaster
from app.models.frame_type_master_model import FrameTypeMaster
from app.models.inspection_agency_master_model import InspectionAgencyMaster
from app.models.size_master_model import SizeMaster
from app.models.pump_master_model import PumpMaster
from app.models.mawp_master_model import MawpMaster
from app.models.ownership_master_model import OwnershipMaster
from app.models.product_master_model import ProductMaster
from app.models.safety_valve_brand_model import SafetyValveBrand
from app.models.master_valve_model import MasterValve
from app.models.master_gauge_model import MasterGauge

router = APIRouter(prefix="/api/master", tags=["Master Data"])

@router.get("/all")
def get_all_masters(db: Session = Depends(get_db)):
    return {
        # FIX: Return dictionaries with 'id' and 'name' instead of just strings
        "manufacturer": [
            {"id": row.manufacturer_id, "name": row.manufacturer_name} 
            for row in db.query(ManufacturerMaster).all()
        ],
        "standard": [
            {"id": row.id, "name": row.standard_name} 
            for row in db.query(StandardMaster).all()
        ],
        "tankcode_iso": [
            {"id": row.id, "name": row.tankcode_iso} 
            for row in db.query(TankCodeISOMaster).all()
        ],
        "un__code": [
            {"id": row.id, "code": row.un_code} 
            for row in db.query(UNISOCODEMaster).all()
        ],
        "design_temperature": [
            {"id": row.id, "name": row.design_temperature} 
            for row in db.query(DesignTemperatureMaster).all()
        ],
        "cabinet": [
            {"id": row.id, "name": row.cabinet_type} 
            for row in db.query(CabinetTypeMaster).all()
        ],
        "frame_type": [
            {"id": row.id, "name": row.frame_type} 
            for row in db.query(FrameTypeMaster).all()
        ],
        "inspection_agency": [
            {"id": row.id, "agency_name": row.agency_name} 
            for row in db.query(InspectionAgencyMaster).all()
        ],
        "size": [
            {"id": row.id, "code": row.size_code, "label": row.size_label} 
            for row in db.query(SizeMaster).all()
        ],
        "pump": [
            {"id": row.id, "name": row.pump_value} 
            for row in db.query(PumpMaster).all()
        ],
        "mawp": [
            {"id": row.id, "name": row.mawp_value} 
            for row in db.query(MawpMaster).all()
        ],
        "ownership": [
            {"id": row.id, "name": row.ownership_name} 
            for row in db.query(OwnershipMaster).all()
        ],
        "products": [
            {"id": row.id, "name": row.product_name}
            for row in db.query(ProductMaster).all()
        ],
        "safety_valve_brands": [
            {"id": row.id, "name": row.brand_name}
            for row in db.query(SafetyValveBrand).all()
        ],
        "master_valves": [
            {"id": row.id, "name": row.valve_name, "status": row.status}
            for row in db.query(MasterValve).all()
        ],
        "master_gauges": [
            {"id": row.id, "name": row.gauge_name, "status": row.status}
            for row in db.query(MasterGauge).all()
        ],
    }