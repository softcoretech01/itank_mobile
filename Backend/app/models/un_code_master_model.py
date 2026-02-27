from sqlalchemy import Column, Integer, String
from app.database import Base

class UNISOCODEMaster(Base):
    __tablename__ = "un_code_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    un_code = Column(String(50), nullable=False, unique=True)
