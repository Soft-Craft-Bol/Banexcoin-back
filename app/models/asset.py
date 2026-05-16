from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)

    transactions = relationship("Transaction", back_populates="asset")