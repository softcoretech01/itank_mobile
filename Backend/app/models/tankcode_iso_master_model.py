from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class TankCodeISOMaster(Base):
    __tablename__ = "tankcode_iso_master"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tankcode_iso = Column(String(255), nullable=False, unique=True)
    status = Column(Integer, default=1)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    modified_by = Column(String(100))
    modified_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
