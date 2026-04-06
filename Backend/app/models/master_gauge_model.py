from sqlalchemy import Column, Integer, String
from app.database import Base

class MasterGauge(Base):
    __tablename__ = "master_gauge"

    id = Column(Integer, primary_key=True, index=True)
    gauge_name = Column(String(255), nullable=False, unique=True)
    status = Column(Integer, default=1)
