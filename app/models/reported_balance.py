from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON
from datetime import datetime

from app.core.database import Base


class ReportedBalance(Base):
    __tablename__ = "reported_balances"

    id = Column(Integer, primary_key=True, index=True)

    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)

    client = Column(String, nullable=True)
    asset = Column(String, nullable=True, default="USDT")
    service = Column(String, nullable=True)

    debit = Column(Numeric(18, 8), nullable=True)
    credit = Column(Numeric(18, 8), nullable=True)

    initial_balance = Column(Numeric(18, 8), nullable=True)
    reported_balance = Column(Numeric(18, 8), nullable=True)

    period = Column(String, nullable=True)
    balance_type = Column(String, nullable=False, default="reported_final")

    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)