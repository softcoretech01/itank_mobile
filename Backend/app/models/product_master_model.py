from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.database import Base


class ProductMaster(Base):
    __tablename__ = "product_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
