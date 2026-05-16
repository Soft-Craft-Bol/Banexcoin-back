import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.upload import Upload
from app.models.data_source import DataSource
from app.services.excel_service import read_financial_file

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = "app/uploads"


@router.post("/")
async def upload_file(
    data_source_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()

    if not data_source:
        raise HTTPException(status_code=404, detail="Fuente de datos no encontrada")

    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV o Excel")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    db_upload = Upload(
        filename=file.filename,
        file_type=file.filename.split(".")[-1],
        data_source_id=data_source_id
    )

    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)

    df = read_financial_file(file_path)

    return {
        "id": db_upload.id,
        "filename": file.filename,
        "data_source_id": data_source_id,
        "data_source": data_source.name,
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict(orient="records")
    }