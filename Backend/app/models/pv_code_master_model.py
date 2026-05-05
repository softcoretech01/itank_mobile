from sqlalchemy import Column, Integer, String
from app.database import Base

class PVCodeMaster(Base):
    __tablename__ = "pv_code_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pv_name = Column(String(100), nullable=False, unique=True)
