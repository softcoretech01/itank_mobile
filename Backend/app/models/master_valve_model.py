from sqlalchemy import Column, Integer, String
from app.database import Base

class MasterValve(Base):
    __tablename__ = "master_valve"

    id = Column(Integer, primary_key=True, index=True)
    valve_name = Column(String(255), nullable=False, unique=True)
    status = Column(Integer, default=1)
