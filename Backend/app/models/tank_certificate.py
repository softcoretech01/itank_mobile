from sqlalchemy import Column, Integer, SmallInteger, String, TIMESTAMP, func, ForeignKey
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

    # --- PDF upload paths ---
    periodic_inspection_pdf_path = Column(String(255), nullable=True)
    periodic_inspection_pdf_name = Column(String(255), nullable=True)

    next_insp_pdf_path = Column(String(255), nullable=True)
    next_insp_pdf_name = Column(String(255), nullable=True)

    new_certificate_file = Column(String(255), nullable=True)
    new_certificate_file_name = Column(String(255), nullable=True)

    old_certificate_file = Column(String(255), nullable=True)
    old_certificate_file_name = Column(String(255), nullable=True)

    # 1 = Active, 0 = Inactive
    status = Column(SmallInteger, nullable=False, default=1, server_default="1")

    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())