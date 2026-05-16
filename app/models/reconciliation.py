from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, nullable=True)

    source_a = Column(String, nullable=False)
    source_b = Column(String, nullable=False)

    total_a = Column(Float, default=0)
    total_b = Column(Float, default=0)
    difference = Column(Float, default=0)

    status = Column(String, default="pending")
    details = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)