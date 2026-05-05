from sqlalchemy import Column, Integer, String, DateTime, func, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class TankFrameOuter(Base):
    __tablename__ = "tank_frame_outer"
    
    id = Column(Integer, primary_key=True, index=True)
    ga_reference = Column(String(255), nullable=True)
    ga_image_path = Column(String(255), nullable=True)
    ga_thumbnail_path = Column(String(255), nullable=True)
    image2_image_path = Column(String(255), nullable=True)
    image2_thumbnail_path = Column(String(255), nullable=True)

    img3_path = Column(String(255), nullable=True)
    img4_path = Column(String(255), nullable=True)
    img5_path = Column(String(255), nullable=True)
    img6_path = Column(String(255), nullable=True)
    
    status = Column(SmallInteger, default=1) # 1=Active, 0=Inactive

    remarks = Column(String(30), nullable=True)

    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100), nullable=True)
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    modified_by = Column(String(100), nullable=True)

    # Relationship
