# app/models/inspection_history_model.py
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Numeric, Text, DateTime, Date, func, Index, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from app.database import Base

class InspectionHistory(Base):
    __tablename__ = "inspection_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(Integer, nullable=False, index=True)
    inspection_date = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    report_number = Column(String(50), nullable=False, index=True)
    tank_id = Column(Integer, nullable=True, index=True)
    tank_number = Column(String(50), nullable=False, index=True)
    status_id = Column(Integer, nullable=True, index=True)
    product_id = Column(Integer, nullable=True, index=True)
    inspection_type_id = Column(Integer, nullable=True)
    location_id = Column(Integer, nullable=True)
    working_pressure = Column(String(50), nullable=True)
    design_temperature = Column(String(50), nullable=True)
    frame_type = Column(String(255))
    cabinet_type = Column(String(255))
    mfgr = Column(String(255))
    safety_valve_brand_id = Column(Integer, nullable=True, index=True)
    safety_valve_model_id = Column(Integer, nullable=True, index=True)
    safety_valve_size_id = Column(Integer, nullable=True, index=True)
    # Store next inspection as YYYY/MM (string) to accept year/month input format
    pi_next_inspection_date = Column(String(7))
    notes = Column(Text)
    lifter_weight = Column(String(255), nullable=True)
    lifter_weight_thumbnail = Column(String(255), nullable=True)
    vacuum_reading = Column(String(50), nullable=True)
    vacuum_uom = Column(String(20), nullable=True)
    lifter_weight_value = Column(String(50), nullable=True)
    emp_id = Column(Integer, nullable=True, index=True)
    operator_id = Column(Integer, nullable=True, index=True)
    ownership = Column(String(16), nullable=True, index=True)
    is_submitted = Column(Integer, nullable=False, default=0)
    is_reviewed = Column(Integer, nullable=False, default=0)
    reviewed_by = Column(Integer, nullable=True)
    web_submitted = Column(Integer, nullable=False, default=0)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    history_date = Column(DateTime, nullable=False, default=func.now())

    def __repr__(self):
        return (
            f"<InspectionHistory(id={self.id}, inspection_id={self.inspection_id}, "
            f"report_number='{self.report_number}', tank_number='{self.tank_number}')>"
        )

__table_args__ = (
    Index('idx_inspection_history_inspection_id', 'inspection_id'),
    Index('idx_inspection_history_tank_number', 'tank_number'),
    Index('idx_inspection_history_report_number', 'report_number'),
    Index('idx_inspection_history_history_date', 'history_date'),
)