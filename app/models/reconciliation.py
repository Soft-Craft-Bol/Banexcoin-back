from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from datetime import datetime
from app.core.database import Base


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(Integer, primary_key=True, index=True)

    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)

    operation_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    reconciliation_type = Column(String, nullable=False)
    reference = Column(String, nullable=True)

    operation_amount = Column(Numeric(18, 2), nullable=True)
    bank_amount = Column(Numeric(18, 2), nullable=True)
    difference = Column(Numeric(18, 2), nullable=True)

    status = Column(String, nullable=False)
    message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)