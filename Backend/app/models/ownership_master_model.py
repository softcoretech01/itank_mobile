from sqlalchemy import Column, Integer, String
from app.database import Base

class OwnershipMaster(Base):
    __tablename__ = "ownership_master"
    id = Column(Integer, primary_key=True, index=True)
    ownership_name = Column(String(100), unique=True, nullable=False)