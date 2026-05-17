from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_
from app.models.reconciliation import Reconciliation
from app.models.transaction import Transaction
from math import ceil
from fastapi import Query

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
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return get_reconciliations(
        db=db,
        upload_id=upload_id,
        status=status,
        page=page,
        size=size,
    )

@router.get("/summary/by-type")
def reconciliation_summary_by_type(
    upload_id: int,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(
            Reconciliation.reconciliation_type,
            Reconciliation.status,
            func.count(Reconciliation.id).label("total")
        )
        .filter(Reconciliation.upload_id == upload_id)
        .group_by(
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
        .order_by(
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
        .all()
    )

    return [
        {
            "reconciliation_type": row.reconciliation_type,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

@router.get("/summary/by-client")
def reconciliation_summary_by_client(
    upload_id: int,
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    rows = (
        db.query(
            func.coalesce(OperationTx.client, BankTx.client, "SIN_CLIENTE").label("client"),
            Reconciliation.reconciliation_type,
            Reconciliation.status,
            func.count(Reconciliation.id).label("total")
        )
        .outerjoin(
            OperationTx,
            Reconciliation.operation_transaction_id == OperationTx.id
        )
        .outerjoin(
            BankTx,
            Reconciliation.bank_transaction_id == BankTx.id
        )
        .filter(Reconciliation.upload_id == upload_id)
        .group_by(
            func.coalesce(OperationTx.client, BankTx.client, "SIN_CLIENTE"),
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
        .order_by(
            func.coalesce(OperationTx.client, BankTx.client, "SIN_CLIENTE"),
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
        .all()
    )

    return [
        {
            "client": row.client,
            "reconciliation_type": row.reconciliation_type,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

@router.get("/client/{client_name}/details")
def reconciliation_client_details(
    client_name: str,
    upload_id: int,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    query = (
        db.query(
            Reconciliation,
            OperationTx,
            BankTx
        )
        .outerjoin(
            OperationTx,
            Reconciliation.operation_transaction_id == OperationTx.id
        )
        .outerjoin(
            BankTx,
            Reconciliation.bank_transaction_id == BankTx.id
        )
        .filter(Reconciliation.upload_id == upload_id)
        .filter(
            or_(
                OperationTx.client == client_name,
                BankTx.client == client_name
            )
        )
    )

    if status:
        query = query.filter(Reconciliation.status == status)

    rows = query.order_by(Reconciliation.created_at.desc()).all()

    return [
        {
            "reconciliation": {
                "id": reconciliation.id,
                "reconciliation_type": reconciliation.reconciliation_type,
                "status": reconciliation.status,
                "reference": reconciliation.reference,
                "operation_amount": reconciliation.operation_amount,
                "bank_amount": reconciliation.bank_amount,
                "difference": reconciliation.difference,
                "message": reconciliation.message,
                "created_at": reconciliation.created_at,
            },
            "operation_transaction": {
                "id": operation_tx.id,
                "service_type": operation_tx.service_type,
                "client": operation_tx.client,
                "date": operation_tx.date,
                "asset": operation_tx.asset,
                "amount": operation_tx.amount,
                "fiat_currency": operation_tx.fiat_currency,
                "fiat_amount": operation_tx.fiat_amount,
                "direction": operation_tx.direction,
                "reference": operation_tx.reference,
                "status": operation_tx.status,
                "raw_data": operation_tx.raw_data,
            } if operation_tx else None,
            "bank_transaction": {
                "id": bank_tx.id,
                "service_type": bank_tx.service_type,
                "client": bank_tx.client,
                "date": bank_tx.date,
                "asset": bank_tx.asset,
                "amount": bank_tx.amount,
                "fiat_currency": bank_tx.fiat_currency,
                "fiat_amount": bank_tx.fiat_amount,
                "direction": bank_tx.direction,
                "reference": bank_tx.reference,
                "status": bank_tx.status,
                "raw_data": bank_tx.raw_data,
            } if bank_tx else None,
        }
        for reconciliation, operation_tx, bank_tx in rows
    ]

@router.get("/errors")
def reconciliation_errors(
    upload_id: int,
    status: str | None = None,
    client: str | None = None,
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    query = (
        db.query(
            Reconciliation,
            OperationTx,
            BankTx
        )
        .outerjoin(
            OperationTx,
            Reconciliation.operation_transaction_id == OperationTx.id
        )
        .outerjoin(
            BankTx,
            Reconciliation.bank_transaction_id == BankTx.id
        )
        .filter(Reconciliation.upload_id == upload_id)
        .filter(Reconciliation.status != "MATCHED")
    )

    if status:
        query = query.filter(Reconciliation.status == status)

    if client:
        query = query.filter(
            or_(
                OperationTx.client == client,
                BankTx.client == client
            )
        )

    rows = query.order_by(
        Reconciliation.status,
        Reconciliation.reconciliation_type,
        Reconciliation.reference
    ).all()

    return [
        {
            "client": operation_tx.client if operation_tx else bank_tx.client if bank_tx else None,
            "reconciliation_id": reconciliation.id,
            "reconciliation_type": reconciliation.reconciliation_type,
            "status": reconciliation.status,
            "reference": reconciliation.reference,
            "operation_amount": reconciliation.operation_amount,
            "bank_amount": reconciliation.bank_amount,
            "difference": reconciliation.difference,
            "message": reconciliation.message,
            "operation_transaction": {
                "id": operation_tx.id,
                "service_type": operation_tx.service_type,
                "client": operation_tx.client,
                "date": operation_tx.date,
                "amount": operation_tx.amount,
                "fiat_amount": operation_tx.fiat_amount,
                "reference": operation_tx.reference,
                "raw_data": operation_tx.raw_data,
            } if operation_tx else None,
            "bank_transaction": {
                "id": bank_tx.id,
                "service_type": bank_tx.service_type,
                "client": bank_tx.client,
                "date": bank_tx.date,
                "amount": bank_tx.amount,
                "fiat_amount": bank_tx.fiat_amount,
                "reference": bank_tx.reference,
                "raw_data": bank_tx.raw_data,
            } if bank_tx else None,
        }
        for reconciliation, operation_tx, bank_tx in rows
    ]

@router.get("/errors/by-client")
def reconciliation_errors_by_client(
    upload_id: int,
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    rows = (
        db.query(
            func.coalesce(OperationTx.client, BankTx.client, "SIN_CLIENTE").label("client"),
            Reconciliation.status,
            func.count(Reconciliation.id).label("total")
        )
        .outerjoin(
            OperationTx,
            Reconciliation.operation_transaction_id == OperationTx.id
        )
        .outerjoin(
            BankTx,
            Reconciliation.bank_transaction_id == BankTx.id
        )
        .filter(Reconciliation.upload_id == upload_id)
        .filter(Reconciliation.status != "MATCHED")
        .group_by(
            func.coalesce(OperationTx.client, BankTx.client, "SIN_CLIENTE"),
            Reconciliation.status
        )
        .order_by(func.count(Reconciliation.id).desc())
        .all()
    )

    return [
        {
            "client": row.client,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]