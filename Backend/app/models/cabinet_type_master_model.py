from sqlalchemy import Column, Integer, String
from app.database import Base

class CabinetTypeMaster(Base):
    __tablename__ = "cabinet_type_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cabinet_type = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
