from sqlalchemy import Column, Integer, String
from app.database import Base

class MawpMaster(Base):
    __tablename__ = "mawp_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    mawp_value = Column(String(50), nullable=False, unique=True)
