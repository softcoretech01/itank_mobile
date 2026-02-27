from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from app.database import Base

class CargoTankTransaction(Base):
    __tablename__ = "cargo_tank_transaction"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_details.id", ondelete="CASCADE"), nullable=False)
    cargo_reference = Column(Integer, ForeignKey("cargo_tank_master.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    # New fields
    density = Column(String(100), nullable=True)
    compatability_notes = Column(String(500), nullable=True)
    cargo_master_id = Column(Integer, ForeignKey("cargo_tank_master.id", ondelete="CASCADE"), nullable=True)
    loading_parts = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())