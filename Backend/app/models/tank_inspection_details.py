# app/models/tank_inspection_details.py
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Numeric, Text, DateTime, Date, func, Index, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from app.database import Base

class TankInspectionDetails(Base):
    __tablename__ = "tank_inspection_details"

    inspection_id = Column(Integer, primary_key=True, index=True)
    inspection_date = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    report_number = Column(String(50), nullable=False, unique=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_details.tank_id", ondelete="SET NULL"), nullable=True, index=True)
    tank_number = Column(String(50), nullable=False, index=True)
    status_id = Column(Integer, nullable=True, index=True)
    inspection_type_id = Column(Integer, nullable=True)
    location_id = Column(Integer, nullable=True)
    working_pressure = Column(String(50), nullable=True)
    design_temperature = Column(String(50), nullable=True)
    frame_type = Column(String(255))
    cabinet_type = Column(String(255))
    mfgr = Column(String(255))
    safety_valve_model_id = Column(Integer, nullable=True, index=True)
    safety_valve_size_id = Column(Integer, nullable=True, index=True)
    # Store next inspection as YYYY/MM (string) to accept year/month input format
    pi_next_inspection_date = Column(String(7))
    notes = Column(Text)
    vacuum_reading = Column(String(50), nullable=True)
    vacuum_uom = Column(String(20), nullable=True)
    lifter_weight_value = Column(String(50), nullable=True)
    emp_id = Column(Integer, ForeignKey("users.emp_id"), nullable=True, index=True)
    operator_id = Column(Integer, nullable=True, index=True)
    ownership = Column(String(16), nullable=True, index=True)
    is_submitted = Column(Integer, nullable=False, default=0)
    web_submitted = Column(Integer, nullable=False, default=0)
    is_reviewed = Column(Integer, nullable=False, default=0)
    reviewed_by = Column(Integer, ForeignKey("users.emp_id"), nullable=True)
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Relationship back to inspection_checklist items
    checklists = relationship("InspectionChecklist", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<TankInspectionDetails(inspection_id={self.inspection_id}, "
            f"report_number='{self.report_number}', tank_number='{self.tank_number}')>"
        )

    @property
    def as_dict(self):
        return {
            "inspection_id": self.inspection_id,
            "inspection_date": self.inspection_date.isoformat() if self.inspection_date else None,
            "report_number": self.report_number,
            "tank_number": self.tank_number,
            "status_id": self.status_id,
            "inspection_type_id": self.inspection_type_id,
            "location_id": self.location_id,
            "working_pressure": float(self.working_pressure) if self.working_pressure is not None else None,
            "frame_type": self.frame_type,
            "design_temperature": self.design_temperature,
            "cabinet_type": self.cabinet_type,
            "mfgr": self.mfgr,
            "safety_valve_model_id": self.safety_valve_model_id,
            "safety_valve_size_id": self.safety_valve_size_id,
            "pi_next_inspection_date": self.pi_next_inspection_date if self.pi_next_inspection_date else None,
            "notes": self.notes,
            "vacuum_reading": self.vacuum_reading,
            "vacuum_uom": self.vacuum_uom,
            "lifter_weight_value": self.lifter_weight_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "operator_id": self.operator_id,
            "is_submitted": self.is_submitted,
            "web_submitted": self.web_submitted,
            "is_reviewed": self.is_reviewed,
            "reviewed_by": self.reviewed_by,
            "operator_name": self.operator_name,
            "ownership": self.ownership,
        }

__table_args__ = (
    Index('idx_tank_inspection_tank_number', 'tank_number'),
    Index('idx_tank_inspection_report_number', 'report_number'),
    Index('idx_tank_inspection_inspection_date', 'inspection_date'),
    Index('idx_tank_inspection_operator_id', 'operator_id'),
    Index('idx_tank_inspection_ownership', 'ownership'),
)
