from sqlalchemy import Column, Integer, String
from app.database import Base

class FrameTypeMaster(Base):
    __tablename__ = "frame_type_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    frame_type = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
