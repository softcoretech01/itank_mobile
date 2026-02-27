from sqlalchemy import Column, Integer, String
from app.database import Base

class InspectionAgencyMaster(Base):
    __tablename__ = "inspection_agency_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agency_name = Column(String(50), nullable=False, unique=True)
