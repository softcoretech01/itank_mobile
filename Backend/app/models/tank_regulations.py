from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from app.database import Base

class TankRegulation(Base):
    __tablename__ = "tank_regulations"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"))
    # regulation_id removed; now handled via multiple_regulation table
    initial_approval_no = Column(String(100), nullable=True)
    imo_type = Column(String(100), nullable=True)
    safety_standard = Column(String(255), nullable=True)
    # regulation_name removed; now handled via multiple_regulation table
    country_registration = Column(String(100), nullable=True)
    count = Column(Integer, default=0)  # Number of regulations linked
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())