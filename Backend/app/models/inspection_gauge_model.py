from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class InspectionGauge(Base):
    __tablename__ = "inspection_gauge"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_details.tank_id"), nullable=False)
    features = Column(String(255), nullable=True)
    status_id = Column(Integer, ForeignKey("inspection_status.status_id"), nullable=True)
    status = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100), nullable=True)
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    modified_by = Column(String(100), nullable=True)

    # Relationship to TankDetails if needed
    # tank = relationship("TankDetails", back_populates="gauges") 
    # Relationship to InspectionStatus
    # status_rel = relationship("InspectionStatus")
