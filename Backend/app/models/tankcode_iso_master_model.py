from sqlalchemy import Column, Integer, String
from app.database import Base

class TankCodeISOMaster(Base):
    __tablename__ = "tankcode_iso_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tankcode_iso = Column(String(50), nullable=False, unique=True)
