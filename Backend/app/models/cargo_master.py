from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.database import Base

class CargoTankMaster(Base):
    __tablename__ = "cargo_tank_master"

    id = Column(Integer, primary_key=True, index=True)
    cargo_reference = Column(String(100), nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
