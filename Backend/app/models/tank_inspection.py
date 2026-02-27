from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, func, ForeignKey
from app.database import Base # <-- CORRECT: Import the single, central Base object


class TankInspection(Base):
    __tablename__ = "tank_inspection"

    id = Column(Integer, primary_key=True, index=True)
    
    # FIX: Must be a ForeignKey pointing to the main tank header
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False) 
    
    insp_2_5y_date = Column(Date, nullable=True)
    next_insp_date = Column(Date, nullable=True)
    tank_certificate = Column(String(255), nullable=True)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())