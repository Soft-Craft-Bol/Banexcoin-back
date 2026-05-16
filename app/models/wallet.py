from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    network = Column(String, nullable=True)
    address = Column(String, nullable=True)
    balance = Column(Float, default=0)
    currency = Column(String, default="USDT")
    created_at = Column(DateTime, default=datetime.utcnow)
