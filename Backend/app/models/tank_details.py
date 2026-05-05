from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey, Date, DateTime, func
from app.database import Base

class TankDetails(Base):
    __tablename__ = "tank_details"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id"), unique=True, index=True)
    tank_number = Column(String(50), nullable=False)
    tank_iso_code = Column(String(255), nullable=True)  # ISO code label from master
    # Allow multiple standard names stored as comma-separated values
    standard = Column(String(255), nullable=True)       # Standard label(s) from master
    pv_id = Column(Integer, nullable=True)             # Pressure Vessel Code ID from master
    status = Column(String(20), default="active", nullable=False)
    mfgr = Column(String(255))       
    initial_test = Column(String(7), nullable=True)                   # Manufacturer label from master
    date_mfg = Column(String(7), nullable=True)         # MM/YYYY format as string
    un_code = Column(Text)  # User-entered UN codes, comma-separated (e.g., '1977,2313')
    capacity_l = Column(Float)
    mawp = Column(String(50), nullable=True)            # Accepts values like '24.0 bar'
    design_temperature = Column(String(50), nullable=True) # Design temperature label from master
    tare_weight_kg = Column(Float)
    mgw_kg = Column(Float)
    mpl_kg = Column(Float)
    size = Column(String(100))                          # Size label from master
    pump_type = Column(String(100))                     # Pump type label from master
    gross_kg = Column(Float)
    net_kg = Column(Float)
    working_pressure = Column(String(50), nullable=True) # Accepts values like '4.0 bar'
    cabinet_type = Column(String(100), nullable=True)    # Cabinet type label from master
    frame_type = Column(String(100), nullable=True)      # Frame type label from master
    color_body_frame = Column(String(100), nullable=True)
    evacuation_valve = Column(String(100), nullable=True)
    product_id = Column(Text, index=True, nullable=True)
    safety_valve_brand_id = Column(Integer, index=True)
    pid_id = Column(Integer, index=True, nullable=True)
    ga_id = Column(Integer, index=True, nullable=True)
    tank_number_image_path = Column(String(255), nullable=True)
    remark = Column(Text, nullable=True)
    remark2 = Column(Text, nullable=True)
    ownership = Column(String(100), nullable=True)  # Ownership name from ownership_master
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=False)
    #created_at = Column(DateTime, default=func.now())
    #updated_at = Column(DateTime, default=func.now(), onupdate=func.now())