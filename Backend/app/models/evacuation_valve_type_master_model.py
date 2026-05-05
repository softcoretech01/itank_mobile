from sqlalchemy import Column, Integer, String
from app.database import Base

class EvacuationValveTypeMaster(Base):
    __tablename__ = "evacuation_valve_type_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evacuation_valve_type = Column(String(100), nullable=False, unique=True)
