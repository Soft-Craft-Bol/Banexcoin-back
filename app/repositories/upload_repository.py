from sqlalchemy.orm import Session
from app.models.upload import Upload

def create_upload(db: Session, data: dict):
    upload = Upload(**data)
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload

def get_uploads(db: Session):
    return db.query(Upload).order_by(Upload.created_at.desc()).all()

def update_upload_status(db: Session, upload: Upload, status: str, rows_count: int = 0, error_message: str | None = None):
    upload.status = status
    upload.rows_count = rows_count
    upload.error_message = error_message
    db.commit()
    db.refresh(upload)
    return upload