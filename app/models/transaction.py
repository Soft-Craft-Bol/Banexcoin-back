from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)

    sheet_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    service_type = Column(String, nullable=True)

    client = Column(String, nullable=True)

    date = Column(DateTime, nullable=True)

    asset = Column(String, nullable=True)          # Ej: USDT
    amount = Column(Numeric(18, 8), nullable=True) # Monto cripto

    fiat_currency = Column(String, nullable=True)  # Ej: BOB
    fiat_amount = Column(Numeric(18, 2), nullable=True)

    direction = Column(String, nullable=True)      # in, out, internal, bank_in, bank_out
    reference = Column(String, nullable=True)
    status = Column(String, nullable=True)

    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)