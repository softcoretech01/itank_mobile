from sqlalchemy import Column, Integer, String
from app.database import Base

class ColorBodyFrameMaster(Base):
    __tablename__ = "color_body_frame_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    color_body_frame = Column(String(100), nullable=False, unique=True)
