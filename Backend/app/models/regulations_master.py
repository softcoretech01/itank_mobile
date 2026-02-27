from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class RegulationsMaster(Base):
    __tablename__ = "regulations_master"

    id = Column(Integer, primary_key=True, index=True)
    regulation_name = Column(String(100), unique=True, nullable=False)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
