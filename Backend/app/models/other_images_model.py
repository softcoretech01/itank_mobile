from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from app.database import Base

class TankOtherImage(Base):
    __tablename__ = "tank_other_images"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_details.id"), nullable=False)
    image_name = Column(String(50), nullable=False)  # e.g. "image_1", "image_2"
    image_path = Column(String(255), nullable=True)
    thumbnail_path = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(50), nullable=True)
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    modified_by = Column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint('tank_id', 'image_name', name='unique_tank_image'),
    )
