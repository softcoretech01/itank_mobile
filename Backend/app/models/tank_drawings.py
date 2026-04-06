from sqlalchemy import Column, Integer, SmallInteger, String, TIMESTAMP, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class TankDrawing(Base):
    __tablename__ = "tank_drawings"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False)

    # Text reference fields
    pid_reference = Column(String(255), nullable=True)
    ga_drawing = Column(String(255), nullable=True)

    # JPEG image uploads: P&ID Drawing and GA Drawing
    pid_drawing = Column(String(255), nullable=True)          # stored path/S3 key
    pid_drawing_name = Column(String(255), nullable=True)     # original filename

    ga_drawing_file = Column(String(255), nullable=True)      # stored path/S3 key
    ga_drawing_file_name = Column(String(255), nullable=True) # original filename

    # 1 = Active, 0 = Inactive
    status = Column(SmallInteger, nullable=False, default=1, server_default="1")

    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    from app.models.tank_header import Tank
    tank = relationship("Tank")