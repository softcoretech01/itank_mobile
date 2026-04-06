from sqlalchemy.orm import Session
from app.models.cargo_master import CargoTankMaster
from app.models.role_master_model import RoleMaster
from app.models.role_rights_model import RoleRights

def init_seed_data(db: Session):
                
            
        
    """
    Checks if tables are empty and populates them with initial 5 values.
    """
    
    # --- 1. Ensure CargoTankMaster table exists and seed ---
    try:
        CargoTankMaster.__table__.create(db.get_bind(), checkfirst=True)
        if not db.query(CargoTankMaster).first():
            print("Seeding CargoTankMaster data...")
            cargo_tanks = [
                CargoTankMaster(cargo_reference="CT-Alpha-01"),
                CargoTankMaster(cargo_reference="CT-Bravo-02"),
                CargoTankMaster(cargo_reference="LNG-Storage-05"),
                CargoTankMaster(cargo_reference="LPG-Transport-09"),
                CargoTankMaster(cargo_reference="Chem-Residue-X1"),
            ]
            db.add_all(cargo_tanks)
            db.commit()
            print("CargoTankMaster seeded successfully.")
        else:
            print("CargoTankMaster data already exists. Skipping.")
    except Exception as e:
        print(f"Error seeding CargoTankMaster: {e}")
        db.rollback()

        # --- 3. Ensure ManufacturerMaster table exists and seed ---
    try:
        from app.models.manufacturer_master_model import ManufacturerMaster
        ManufacturerMaster.__table__.create(db.get_bind(), checkfirst=True)
        if not db.query(ManufacturerMaster).first():
            print("Seeding ManufacturerMaster data...")
            manufacturers = [
                ManufacturerMaster(manufacturer_name="SZHF"),
                ManufacturerMaster(manufacturer_name="JXOX"),
                ManufacturerMaster(manufacturer_name="WnD"),
                ManufacturerMaster(manufacturer_name="CIMC"),
            ]
            db.add_all(manufacturers)
            db.commit()
            print("ManufacturerMaster seeded successfully.")
        else:
            print("ManufacturerMaster data already exists. Skipping.")
    except Exception as e:
        print(f"Error seeding ManufacturerMaster: {e}")
        db.rollback()
    
        # --- 4. Ensure StandardMaster table exists and seed ---
    try:
        from app.models.standard_master_model import StandardMaster
        standards = ["CSC", "IMDG", "RID", "ADR", "CCC","USDOT","TC","UIC","TIR","IRS 50592"]
        StandardMaster.__table__.create(db.get_bind(), checkfirst=True)
        for s in standards:
            if not db.query(StandardMaster).filter_by(standard_name=s).first():
                db.add(StandardMaster(standard_name=s))
        db.commit()
        print("StandardMaster seeded successfully.")    
                              
    except Exception as e:
            print(f"Error seeding StandardMaster: {e}")
            db.rollback()
        
    try:
        from app.models.mawp_master_model import MawpMaster
        mawp_values = ["21.4 bar", "22.0 bar", "24.0 bar"]
        MawpMaster.__table__.create(db.get_bind(), checkfirst=True)
        for m in mawp_values:
            if not db.query(MawpMaster).filter_by(mawp_value=m).first():
                db.add(MawpMaster(mawp_value=m))
        db.commit()
        print("MawpMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding MawpMaster: {e}")
        db.rollback()
        
        # --- 6. Seed DesignTemperatureMaster ---
    try:
        from app.models.design_temperature_master_model import DesignTemperatureMaster
        temps = ["-40 C to 50 C", "-196 C to 50 C"]
        DesignTemperatureMaster.__table__.create(db.get_bind(), checkfirst=True)
        for t in temps:
            if not db.query(DesignTemperatureMaster).filter_by(design_temperature=t).first():
                db.add(DesignTemperatureMaster(design_temperature=t))
                        
        db.commit()
        print("DesignTemperatureMaster seeded successfully.")        
    except Exception as e:
        print(f"Error seeding DesignTemperatureMaster: {e}")
        db.rollback()

    # --- 7. Seed SizeMaster ---
    try:
        from app.models.size_master_model import SizeMaster
        sizes = [
            {"size_code": "22", "size_label": "20 Feet * 8 Feet"},
            {"size_code": "25", "size_label": "20 Feet * 9 Feet"},
            {"size_code": "42", "size_label": "40 Feet * 8 Feet"},
            {"size_code": "45", "size_label": "40 Feet * 9 Feet"},
            {"size_code": "52", "size_label": "45 Feet* 8 Feet"},
            {"size_code": "55", "size_label": "45 Feet* 9 Feet"},
            {"size_code": "M2", "size_label": "48 Feet * 8 Feet"},
            {"size_code": "M5", "size_label": "48 Feet * 9 Feet"},
        ]
        SizeMaster.__table__.create(db.get_bind(), checkfirst=True)
        for s in sizes:
            if not db.query(SizeMaster).filter_by(size_code=s["size_code"]).first():
                db.add(SizeMaster(size_code=s["size_code"], size_label=s["size_label"]))
        db.commit()
        print("SizeMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding SizeMaster: {e}")
        db.rollback()


    # --- 8. Seed FrameTypeMaster ---
    try:
        from app.models.frame_type_master_model import FrameTypeMaster
        frame_types = [
            {"frame_type": "Frame T-1/Frame Tank", "description": "Cross Member / Frame T-1"},
            {"frame_type": "Frame T-2/Beam Tank", "description": "Cross Member / Frame T-2"},
        ]
        FrameTypeMaster.__table__.create(db.get_bind(), checkfirst=True)
        for ft in frame_types:
            if not db.query(FrameTypeMaster).filter_by(frame_type=ft["frame_type"]).first():
                db.add(FrameTypeMaster(frame_type=ft["frame_type"], description=ft["description"]))
        db.commit()
        print("FrameTypeMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding FrameTypeMaster: {e}")
        db.rollback()


    # --- 9. Seed CabinetTypeMaster ---
    try:
        from app.models.cabinet_type_master_model import CabinetTypeMaster
        cabinet_types = [
            {"cabinet_type": "-", "description": "No cabinet"},
            {"cabinet_type": "Side-1/Full Door", "description": "Cab Door - Side-1"},
            {"cabinet_type": "Side-2/Half Door", "description": "Cab Door - Side-2"},
            {"cabinet_type": "Back", "description": "Cab Door - Back"},
        ]
        CabinetTypeMaster.__table__.create(db.get_bind(), checkfirst=True)
        for ct in cabinet_types:
            if not db.query(CabinetTypeMaster).filter_by(cabinet_type=ct["cabinet_type"]).first():
                db.add(CabinetTypeMaster(cabinet_type=ct["cabinet_type"], description=ct["description"]))
        db.commit()
        print("CabinetTypeMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding CabinetTypeMaster: {e}")
        db.rollback()

    # --- 11. Seed UNISOCODEMaster ---
    try:
        from app.models.un_code_master_model import UNISOCODEMaster
        # Replace existing UN codes with the requested list (store code only)
        un_code_values = [
            "1073",
            "1977",
            "1951",
            "1972",
            "1961",
            "1038",
            "2201",
            "2187",
        ]
        UNISOCODEMaster.__table__.create(db.get_bind(), checkfirst=True)
        for code in un_code_values:
            if not db.query(UNISOCODEMaster).filter_by(un_code=code).first():
                db.add(UNISOCODEMaster(un_code=code))
        db.commit()
        print("UNISOCODEMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding UNISOCODEMaster: {e}")
        db.rollback()
# --- 12. Seed InspectionAgencyMaster ---
    try:
        from app.models.inspection_agency_master_model import InspectionAgencyMaster
        agencies = ["BV", "LR", "DNV", "RNA"]
        InspectionAgencyMaster.__table__.create(db.get_bind(), checkfirst=True)
        for agency in agencies:
            if not db.query(InspectionAgencyMaster).filter_by(agency_name=agency).first():
                db.add(InspectionAgencyMaster(agency_name=agency))
        db.commit()
        print("InspectionAgencyMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding InspectionAgencyMaster: {e}")
        db.rollback()

    # --- 13. Seed PumpMaster ---
    try:
        from app.models.pump_master_model import PumpMaster
        pump_values = ["Yes", "No"]
        PumpMaster.__table__.create(db.get_bind(), checkfirst=True)
        for val in pump_values:
            if not db.query(PumpMaster).filter_by(pump_value=val).first():
                db.add(PumpMaster(pump_value=val))
        db.commit()
        print("PumpMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding PumpMaster: {e}")
        db.rollback()
# --- Seed OwnershipMaster ---
    try:
        from app.models.ownership_master_model import OwnershipMaster
        ownerships = ["albatross", "Smart Gas", "ABC1"]
        OwnershipMaster.__table__.create(db.get_bind(), checkfirst=True)
        for name in ownerships:
            if not db.query(OwnershipMaster).filter_by(ownership_name=name).first():
                db.add(OwnershipMaster(ownership_name=name))
        db.commit()
        print("OwnershipMaster seeded successfully.")
    except Exception as e:
        print(f"Error seeding OwnershipMaster: {e}")
        db.rollback()

    # --- Seed RoleMaster ---
    try:
        RoleMaster.__table__.create(db.get_bind(), checkfirst=True)
        if not db.query(RoleMaster).first():
            print("Seeding RoleMaster data...")
            roles = [
                RoleMaster(role_name="ADMIN"),
                RoleMaster(role_name="OPERATOR"),
                RoleMaster(role_name="GUEST"),
                RoleMaster(role_name="STAFFS"),
            ]
            db.add_all(roles)
            db.commit()
            print("RoleMaster seeded successfully.")
        else:
            print("RoleMaster data already exists. Skipping.")
    except Exception as e:
        print(f"Error seeding RoleMaster: {e}")
        db.rollback()

    # --- Seed RoleRights ---
    try:
        RoleRights.__table__.create(db.get_bind(), checkfirst=True)
        if not db.query(RoleRights).first():
            print("Seeding RoleRights data...")
            rights = [
                RoleRights(user_role_id=1, module_access='Web Application', screen='Tank details', read_only=True, edit_only=True),
                RoleRights(user_role_id=1, module_access='Mobile Application', screen='Inspection Report', read_only=True, edit_only=True),
                RoleRights(user_role_id=1, module_access='Web Application', screen='Inspection Report', read_only=True, edit_only=True),
                RoleRights(user_role_id=1, module_access='Web Application', screen='Generate PPT', read_only=True, edit_only=True),
                RoleRights(user_role_id=3, module_access='Web Application', screen='Tank details', read_only=True, edit_only=True),
                RoleRights(user_role_id=3, module_access='Mobile Application', screen='Inspection Report', read_only=True, edit_only=True),
                RoleRights(user_role_id=3, module_access='Web Application', screen='Inspection Report', read_only=True, edit_only=True),
                RoleRights(user_role_id=3, module_access='Web Application', screen='Generate PPT', read_only=True, edit_only=True),
                RoleRights(user_role_id=2, module_access='Web Application', screen='Tank details', read_only=False, edit_only=False),
                RoleRights(user_role_id=2, module_access='Mobile Application', screen='Inspection Report', read_only=True, edit_only=True),
                RoleRights(user_role_id=2, module_access='Web Application', screen='Inspection Report', read_only=False, edit_only=False),
                RoleRights(user_role_id=2, module_access='Web Application', screen='Generate PPT', read_only=False, edit_only=False),
                RoleRights(user_role_id=4, module_access='Web Application', screen='Tank details', read_only=False, edit_only=False),
                RoleRights(user_role_id=4, module_access='Mobile Application', screen='Inspection Report', read_only=False, edit_only=False),
                RoleRights(user_role_id=4, module_access='Web Application', screen='Inspection Report', read_only=True, edit_only=True),
                RoleRights(user_role_id=4, module_access='Web Application', screen='Generate PPT', read_only=False, edit_only=False),
            ]
            db.add_all(rights)
            db.commit()
            print("RoleRights seeded successfully.")
        else:
            print("RoleRights data already exists. Skipping.")
    except Exception as e:
        print(f"Error seeding RoleRights: {e}")
        db.rollback()

    # --- Seed MasterValve ---
    try:
        from app.models.master_valve_model import MasterValve
        valves = [
            "Top Fill - Gas", "Emergency Valve - A3", "S/V - 1",
            "Iso - Top Fill", "Trycock - 1", "S/V - 2",
            "Bottom fill - Liq", "Trycock - 2 / 3", "S/V - 3",
            "Iso - Bottom Fill - A3", "Vacuum Valve", "S/V - 4",
            "Iso - Top / Bottom", "T-Couple Valve", "S/V - B.Disc",
            "Drain Valve", "T-Couple DV-6", "S/V Diverter",
            "Blow Valve", "Liq Connection", "Line SRV - 1",
            "PB Valve Inlet", "Gas Connection", "Line SRV - 2",
            "PB Valve Return", "Vent Pipe", "Line SRV - 3",
            "PB Unit", "Pipe / Support", "Line SRV - 4 / 5",
            "Sample Valve", "Check Valve", "Out Ves B.Disc"
        ]
        MasterValve.__table__.create(db.get_bind(), checkfirst=True)
        for v in valves:
            if not db.query(MasterValve).filter_by(valve_name=v).first():
                db.add(MasterValve(valve_name=v))
        db.commit()
        print("MasterValve seeded successfully.")
    except Exception as e:
        print(f"Error seeding MasterValve: {e}")
        db.rollback()

    # --- Seed MasterGauge ---
    try:
        from app.models.master_gauge_model import MasterGauge
        gauges = [
            "Pressure Gauge", "Tank Number", "Top",
            "Liquid Gauge", "Co. Logo", "Bottom",
            "Temp Gauge", "TEIP", "Front",
            "Gas Phase Valve", "Haz Ship Label", "Rear",
            "Liquid Phase Valve", "Handling Label", "Left",
            "Equalizing Valve", "Weight Label", "Right",
            "Pump - Smith", "T-75 / 22K7 Label", "Cross Member",
            "Motor", "Tank P&ID Plate", "Cab Door - Rear",
            "Electrical Panel", "Tank Data Plate", "Cab Door Lock",
            "Electrical Plug", "Tank CSC Plate", "Paint Condition",
            "Pump / Motor Mounting", "Std Identification Label", "Reflective Marking"
        ]
        MasterGauge.__table__.create(db.get_bind(), checkfirst=True)
        for g in gauges:
            if not db.query(MasterGauge).filter_by(gauge_name=g).first():
                db.add(MasterGauge(gauge_name=g))
        db.commit()
        print("MasterGauge seeded successfully.")
    except Exception as e:
        print(f"Error seeding MasterGauge: {e}")
        db.rollback()