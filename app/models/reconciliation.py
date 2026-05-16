from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
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

    # ===== EPICA 5 =====

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    period_type = Column(String, nullable=True)

    data_source_id = Column(
        Integer,
        ForeignKey("data_sources.id"),
        nullable=True
    )

    asset_id = Column(
        Integer,
        ForeignKey("assets.id"),
        nullable=True
    )

    initial_balance = Column(Float, nullable=True)

    reported_final_balance = Column(Float, nullable=True)

    expected_balance = Column(Float, nullable=True)