from sqlalchemy import Column, Integer, String
from app.database import Base

class DesignTemperatureMaster(Base):
    __tablename__ = "design_temperature_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    design_temperature = Column(String(50), nullable=False, unique=True)
