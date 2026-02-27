from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Text
from app.database import Base

class TankDrawing(Base):
    __tablename__ = "tank_drawings"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False)

    # New structure: store P&ID reference, GA drawing text and two image paths
    pid_reference = Column(String(255), nullable=True)
    ga_drawing = Column(String(255), nullable=True)

    pid_image_path = Column(String(255), nullable=True)
    ga_image_path = Column(String(255), nullable=True)
    pid_original_filename = Column(String(255), nullable=True)
    ga_original_filename = Column(String(255), nullable=True)

    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())