from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey
from app.database import Base

class Tank(Base):
    __tablename__ = "tank_header"

    id = Column(Integer, primary_key=True, index=True)
    tank_number = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=False)
