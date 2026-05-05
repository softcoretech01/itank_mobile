from sqlalchemy import Column, Integer, SmallInteger, String, TIMESTAMP, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class TankDrawing(Base):
    __tablename__ = "tank_drawings"

    id = Column(Integer, primary_key=True, index=True)

    # Text reference fields
    pid_reference = Column(String(255), nullable=True, unique=True, index=True)

    # JPEG image uploads: P&ID Drawing and image2 Drawing
    pid_drawing = Column(String(255), nullable=True)          # stored path/S3 key
    pid_drawing_name = Column(String(255), nullable=True)     # original filename

    image2_drawing_file = Column(String(255), nullable=True)      # stored path/S3 key
    image2_drawing_file_name = Column(String(255), nullable=True) # original filename

    img3 = Column(String(255), nullable=True)
    img3_name = Column(String(255), nullable=True)
    img4 = Column(String(255), nullable=True)
    img4_name = Column(String(255), nullable=True)
    img5 = Column(String(255), nullable=True)
    img5_name = Column(String(255), nullable=True)
    img6 = Column(String(255), nullable=True)
    img6_name = Column(String(255), nullable=True)

    # 1 = Active, 0 = Inactive
    status = Column(SmallInteger, nullable=False, default=1, server_default="1")

    remarks = Column(String(30), nullable=True)

    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())