from sqlalchemy import Column, Integer, String, DateTime, func, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class TankValveAndShell(Base):
    __tablename__ = "tank_valve_and_shell"
    
    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), index=True)
    valve_label_image_path = Column(String(255))
    valve_label_thumbnail_path = Column(String(255))
    tank_frame_image_path = Column(String(255))
    tank_frame_thumbnail_path = Column(String(255))
    
    status = Column(SmallInteger, default=1) # 1=Active, 0=Inactive
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100), nullable=True)
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    modified_by = Column(String(100), nullable=True)

    # Relationship
    from app.models.tank_header import Tank
    tank = relationship("Tank")
