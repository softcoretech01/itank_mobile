from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class MultipleRegulation(Base):
    __tablename__ = "multiple_regulation"
    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tank_header.id", ondelete="CASCADE"), nullable=False)
    regulation_id = Column(Integer, ForeignKey("regulations_master.id", ondelete="CASCADE"), nullable=False)
    regulation_name = Column(String(255), nullable=False)
