from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship 
from app.database import Base


class TankCertificate(Base):
    __tablename__ = "tank_certificate"

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. Primary Foreign Key: Use tank_id to link to tank_header.id (Correct and sufficient)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False)
    
    # 2. Regular String column (Retained the fix: removed ForeignKey constraint)
    tank_number = Column(String(50), nullable=False) 
    
    year_of_manufacturing = Column(String(10), nullable=True)
    # Store inspection dates as YYYY/MM (string) to allow year/month inputs
    insp_2_5y_date = Column(String(7), nullable=True)
    next_insp_date = Column(String(7), nullable=True)
    
    # NEW FIELD ADDED HERE
    inspection_agency = Column(String(10), nullable=True)
    
    certificate_number = Column(String(255), nullable=False, unique=True)
    
    periodic_inspection_image_path = Column(String(255), nullable=True)
    next_insp_image_path = Column(String(255), nullable=True)
    
    certificate_file = Column(String(255), nullable=True)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())