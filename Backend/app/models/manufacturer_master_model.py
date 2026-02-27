from sqlalchemy import Column, Integer, String
from app.database import Base

class ManufacturerMaster(Base):
    __tablename__ = "manufacturer_master"

    manufacturer_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_name = Column(String(100), nullable=False, unique=True)
