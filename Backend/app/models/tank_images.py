from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Date, Index, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base

class TankImage(Base):
    __tablename__ = "tank_images"

    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(Integer, ForeignKey("users.emp_id", ondelete="SET NULL"), nullable=True)
    tank_number = Column(String(50), ForeignKey("tank_header.tank_number", ondelete="CASCADE"), nullable=False)
    image_type = Column(String(50), nullable=False)
    image_path = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_date = Column(Date, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint('tank_number', 'image_type', 'created_date', name='uq_tank_image_daily'),
        Index('idx_tank_number', 'tank_number'),
        Index('idx_tank_image_type', 'tank_number', 'image_type'),
        Index('idx_created_date', 'created_date'),
    )

    # Relationships
    user = relationship("User", foreign_keys=[emp_id], lazy="joined")
    tank = relationship("Tank", foreign_keys=[tank_number], lazy="joined")
