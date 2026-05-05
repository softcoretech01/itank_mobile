from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class ScreensMaster(Base):
    __tablename__ = "screens_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String(255), nullable=False)
    screen_name = Column(String(255), nullable=False)
    status = Column(Integer, default=1)
