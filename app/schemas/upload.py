from datetime import datetime
from pydantic import BaseModel

class UploadResponse(BaseModel):
    id: int
    filename: str
    stored_filename: str
    file_type: str
    source: str
    status: str
    rows_count: int
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True