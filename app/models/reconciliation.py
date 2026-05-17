from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(Integer, primary_key=True, index=True)

    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False, index=True)

    operation_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    reconciliation_type = Column(String, nullable=False)
    reference = Column(String, nullable=True)

    operation_amount = Column(Numeric(18, 2), nullable=True)
    bank_amount = Column(Numeric(18, 2), nullable=True)
    difference = Column(Numeric(18, 2), nullable=True)

    status = Column(String, nullable=False, index=True)
    message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index(
            "ix_reconciliations_upload_status_created_at",
            "upload_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_reconciliations_upload_created_at",
            "upload_id",
            "created_at",
        ),
    )