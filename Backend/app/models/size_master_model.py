from sqlalchemy import Column, Integer, String
from app.database import Base

class SizeMaster(Base):
    __tablename__ = "size_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    size_code = Column(String(10), nullable=False, unique=True)
    size_label = Column(String(50), nullable=False)
