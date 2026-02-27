from sqlalchemy import Column, Integer, String
from app.database import Base

class StandardMaster(Base):
    __tablename__ = "standard_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    standard_name = Column(String(100), nullable=False, unique=True)
