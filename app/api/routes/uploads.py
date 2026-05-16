import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.excel_service import read_financial_file

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = "app/uploads"

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV o Excel")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    df = read_financial_file(file_path)

    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict(orient="records")
    }
