from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.upload import Upload
from app.repositories.reconciliation_repository import (
    bulk_create_reconciliations,
    delete_reconciliations_by_upload,
    get_reconciliations,
)
from app.services.reconciliation_service import run_reconciliation


router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/run/{upload_id}")
def run_upload_reconciliation(
    upload_id: int,
    db: Session = Depends(get_db)
):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload no encontrado")

    if upload.status != "processed":
        raise HTTPException(
            status_code=400,
            detail="El archivo todavía no fue procesado correctamente"
        )

    delete_reconciliations_by_upload(db, upload_id)

    results = run_reconciliation(db, upload_id)

    bulk_create_reconciliations(db, results)

    total = len(results)
    matched = len([item for item in results if item["status"] == "MATCHED"])
    differences = len([item for item in results if item["status"] != "MATCHED"])

    return {
        "upload_id": upload_id,
        "total_compared": total,
        "matched": matched,
        "differences": differences,
        "summary": {
            "matched": matched,
            "amount_difference": len([item for item in results if item["status"] == "AMOUNT_DIFFERENCE"]),
            "missing_in_bank": len([item for item in results if item["status"] == "MISSING_IN_BANK"]),
            "missing_in_operation": len([item for item in results if item["status"] == "MISSING_IN_OPERATION"]),
        }
    }


@router.get("/")
def list_reconciliations(
    upload_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    records = get_reconciliations(db, upload_id)

    if status:
        records = [
            item for item in records
            if item.status == status
        ]

    return records