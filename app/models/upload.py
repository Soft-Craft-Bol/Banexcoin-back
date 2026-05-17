from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.database import Base

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    source = Column(String, nullable=False, default="manual")
    status = Column(String, nullable=False, default="pending")
    rows_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

    cloudinary_url = Column(String, nullable=True)
    cloudinary_public_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)