# app/models/role_master_model.py
from sqlalchemy import Column, Integer, String
from app.database import Base


class RoleMaster(Base):
    __tablename__ = "role_master"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(100), nullable=False, unique=True)