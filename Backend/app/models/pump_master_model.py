from sqlalchemy import Column, Integer, String
from app.database import Base

class PumpMaster(Base):
    __tablename__ = "pump_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pump_value = Column(String(10), nullable=False, unique=True)
