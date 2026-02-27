from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ValveTestReport(Base):
    __tablename__ = "valve_test_report"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False)
    inspection_report_file = Column(String(255), nullable=True)
    test_date = Column(Date, nullable=True)
    inspected_by = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    tank = relationship("Tank", foreign_keys=[tank_id], lazy="joined")
