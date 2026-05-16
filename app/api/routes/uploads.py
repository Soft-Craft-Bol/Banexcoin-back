import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.upload import Upload
from app.repositories.upload_repository import create_upload, get_uploads, update_upload_status
from app.schemas.upload import UploadResponse
from app.services.excel_service import SUPPORTED_EXTENSIONS, read_financial_file



router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = "app/uploads"

@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    source: str = Form("manual"),
    db: Session = Depends(get_db)
):
    original_filename = file.filename or "archivo"
    file_extension = os.path.splitext(original_filename)[1].lower()

    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV o Excel")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    stored_filename = f"{uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    upload = create_upload(db, {
        "filename": original_filename,
        "stored_filename": stored_filename,
        "file_type": file_extension.replace(".", ""),
        "source": source,
        "status": "pending",
        "rows_count": 0
    })

    try:
        valid_sheets, sheet_errors = read_financial_file(file_path)

        if not valid_sheets:
            raise ValueError(f"No se pudo procesar ninguna hoja. Errores: {sheet_errors}")

        total_rows = sum(len(df) for df in valid_sheets.values())

        return update_upload_status(
            db=db,
            upload=upload,
            status="processed",
            rows_count=total_rows,
            error_message=None
        )

    except Exception as exc:
        update_upload_status(
            db=db,
            upload=upload,
            status="error",
            rows_count=0,
            error_message=str(exc)
        )

        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/", response_model=list[UploadResponse])
def list_uploaded_files(db: Session = Depends(get_db)):
    return get_uploads(db)


@router.get("/{upload_id}/download")
def download_uploaded_file(
    upload_id: int,
    db: Session = Depends(get_db)
):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    file_path = os.path.join(UPLOAD_DIR, upload.stored_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado")

    return FileResponse(
        path=file_path,
        filename=upload.filename,
        media_type="application/octet-stream"
    )