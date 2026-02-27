# app/models/role_rights_model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RoleRights(Base):
    __tablename__ = "role_rights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_role_id = Column(Integer, ForeignKey('role_master.role_id'), nullable=False)
    module_access = Column(String(100), nullable=False)
    screen = Column(String(100), nullable=False)
    edit_only = Column(Boolean, default=False)
    read_only = Column(Boolean, default=True)

    # Relationship
    role = relationship("RoleMaster", backref="rights")