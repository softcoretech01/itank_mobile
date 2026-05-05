from sqlalchemy import Column, Integer, SmallInteger, String, TIMESTAMP, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class TankCertificate(Base):
    __tablename__ = "tank_certificate"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key: link to tank_header.id
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False)

    # Denormalized tank_number for quick display
    tank_number = Column(String(50), nullable=False)

    year_of_manufacturing = Column(String(10), nullable=True)
    # Store inspection dates as YYYY/MM (string)
    insp_2_5y_date = Column(String(7), nullable=True)
    next_insp_date = Column(String(7), nullable=True)

    inspection_agency = Column(String(10), nullable=True)

    certificate_number = Column(String(255), nullable=False, unique=True)

    # --- certificate upload paths (6 inputs) ---
    initial_certificate_path = Column(String(255), nullable=True)
    initial_certificate_name = Column(String(255), nullable=True)

    certificate1_path = Column(String(255), nullable=True)
    certificate1_name = Column(String(255), nullable=True)

    certificate2_path = Column(String(255), nullable=True)
    certificate2_name = Column(String(255), nullable=True)

    certificate3_path = Column(String(255), nullable=True)
    certificate3_name = Column(String(255), nullable=True)

    certificate4_path = Column(String(255), nullable=True)
    certificate4_name = Column(String(255), nullable=True)

    certificate5_path = Column(String(255), nullable=True)
    certificate5_name = Column(String(255), nullable=True)

    # 1 = Active, 0 = Inactive
    status = Column(SmallInteger, nullable=False, default=1, server_default="1")

    # archives: increments each time an old cert is pushed to the archive pool
    archives = Column(Integer, nullable=False, default=0, server_default="0")

    remarks = Column(String(30), nullable=True)

    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())