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

from math import ceil
from fastapi import Query
from sqlalchemy.orm import aliased
from sqlalchemy import func

@router.get("/summary/by-client")
def reconciliation_summary_by_client(
    upload_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    client_expr = func.coalesce(
        OperationTx.client,
        BankTx.client,
        "SIN_CLIENTE"
    )

    base_query = (
        db.query(
            client_expr.label("client"),
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
            client_expr,
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
    )

    total_elements = base_query.count()
    total_pages = ceil(total_elements / size) if total_elements > 0 else 0

    rows = (
        base_query
        .order_by(
            client_expr,
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
        .offset(page * size)
        .limit(size)
        .all()
    )

    content = [
        {
            "client": row.client,
            "reconciliation_type": row.reconciliation_type,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

    return {
        "content": content,
        "page": page,
        "size": size,
        "totalElements": total_elements,
        "totalPages": total_pages,
        "numberOfElements": len(content),
        "first": page == 0,
        "last": page >= total_pages - 1 if total_pages > 0 else True,
        "empty": len(content) == 0
    }

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
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=500),
    include_raw_data: bool = False,
    db: Session = Depends(get_db),
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    filters = [
        Reconciliation.upload_id == upload_id,
        Reconciliation.status != "MATCHED",
    ]

    if status:
        filters.append(Reconciliation.status == status)

    if client:
        filters.append(
            or_(
                OperationTx.client == client,
                BankTx.client == client,
            )
        )

    base_query = (
        db.query(Reconciliation, OperationTx, BankTx)
        .outerjoin(
            OperationTx,
            Reconciliation.operation_transaction_id == OperationTx.id,
        )
        .outerjoin(
            BankTx,
            Reconciliation.bank_transaction_id == BankTx.id,
        )
        .filter(*filters)
    )

    total_elements = base_query.order_by(None).count()
    total_pages = ceil(total_elements / size) if total_elements else 0
    offset = page * size

    rows = (
        base_query
        .order_by(
            Reconciliation.status,
            Reconciliation.reconciliation_type,
            Reconciliation.reference,
            Reconciliation.id,
        )
        .offset(offset)
        .limit(size)
        .all()
    )

    content = [
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
            "operation_transaction": serialize_transaction(operation_tx, include_raw_data)
            if operation_tx else None,
            "bank_transaction": serialize_transaction(bank_tx, include_raw_data)
            if bank_tx else None,
        }
        for reconciliation, operation_tx, bank_tx in rows
    ]

    return {
        "content": content,
        "pageable": {
            "pageNumber": page,
            "pageSize": size,
            "offset": offset,
            "paged": True,
            "unpaged": False,
        },
        "totalElements": total_elements,
        "totalPages": total_pages,
        "last": page >= total_pages - 1 if total_pages > 0 else True,
        "first": page == 0,
        "size": size,
        "number": page,
        "numberOfElements": len(content),
        "empty": len(content) == 0,
        "sort": {
            "sorted": True,
            "unsorted": False,
            "empty": False,
        },
    }


def serialize_transaction(tx: Transaction, include_raw_data: bool):
    data = {
        "id": tx.id,
        "service_type": tx.service_type,
        "client": tx.client,
        "date": tx.date,
        "amount": tx.amount,
        "fiat_amount": tx.fiat_amount,
        "reference": tx.reference,
    }

    if include_raw_data:
        data["raw_data"] = tx.raw_data

    return data

@router.get("/errors/by-client")
def reconciliation_errors_by_client(
    upload_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    client_expr = func.coalesce(
        OperationTx.client,
        BankTx.client,
        "SIN_CLIENTE"
    )

    base_query = (
        db.query(
            client_expr.label("client"),
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
            client_expr,
            Reconciliation.status
        )
    )

    total_elements = base_query.count()
    total_pages = ceil(total_elements / size) if total_elements > 0 else 0

    rows = (
        base_query
        .order_by(func.count(Reconciliation.id).desc())
        .offset(page * size)
        .limit(size)
        .all()
    )

    content = [
        {
            "client": row.client,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

    return {
        "content": content,
        "page": page,
        "size": size,
        "totalElements": total_elements,
        "totalPages": total_pages,
        "numberOfElements": len(content),
        "first": page == 0,
        "last": page >= total_pages - 1 if total_pages > 0 else True,
        "empty": len(content) == 0
    }

@router.get("/dashboard/stats")
def reconciliation_dashboard_stats(
    upload_id: int | None = None,
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    # Archivos: SIEMPRE cuenta todos los uploads, no por upload_id
    upload_query = db.query(Upload)

    total_files = upload_query.count()

    processed_files = (
        upload_query
        .filter(Upload.status == "processed")
        .count()
    )

    pending_files = (
        upload_query
        .filter(Upload.status.in_(["pending", "uploaded", "processing"]))
        .count()
    )

    error_files = (
        upload_query
        .filter(Upload.status == "error")
        .count()
    )

    # Movimientos: estos sí pueden filtrarse por upload_id
    total_movements_query = db.query(Transaction)

    if upload_id:
        total_movements_query = total_movements_query.filter(
            Transaction.upload_id == upload_id
        )

    total_movements = total_movements_query.count()

    total_clients = (
        total_movements_query
        .filter(Transaction.client.isnot(None))
        .with_entities(func.count(func.distinct(Transaction.client)))
        .scalar()
        or 0
    )

    # Conciliaciones: estas sí pueden filtrarse por upload_id
    reconciliation_query = db.query(Reconciliation)

    if upload_id:
        reconciliation_query = reconciliation_query.filter(
            Reconciliation.upload_id == upload_id
        )

    total_reconciliations = reconciliation_query.count()

    total_errors = (
        reconciliation_query
        .filter(Reconciliation.status != "MATCHED")
        .count()
    )

    matched_total = (
        reconciliation_query
        .filter(Reconciliation.status == "MATCHED")
        .count()
    )

    client_expr = func.coalesce(
        OperationTx.client,
        BankTx.client,
        "SIN_CLIENTE"
    )

    clients_with_errors = (
        db.query(func.count(func.distinct(client_expr)))
        .select_from(Reconciliation)
        .outerjoin(
            OperationTx,
            Reconciliation.operation_transaction_id == OperationTx.id
        )
        .outerjoin(
            BankTx,
            Reconciliation.bank_transaction_id == BankTx.id
        )
        .filter(Reconciliation.status != "MATCHED")
    )

    if upload_id:
        clients_with_errors = clients_with_errors.filter(
            Reconciliation.upload_id == upload_id
        )

    clients_with_errors_count = clients_with_errors.scalar() or 0

    clients_without_errors_count = max(
        total_clients - clients_with_errors_count,
        0
    )

    status_rows = (
        reconciliation_query
        .with_entities(
            Reconciliation.status,
            func.count(Reconciliation.id).label("total")
        )
        .group_by(Reconciliation.status)
        .all()
    )

    status_summary = [
        {
            "status": row.status,
            "total": row.total
        }
        for row in status_rows
    ]

    return {
        "upload_id": upload_id,
        "files": {
            "total": total_files,
            "processed": processed_files,
            "pending": pending_files,
            "errors": error_files
        },
        "clients": {
            "total": total_clients,
            "with_errors": clients_with_errors_count,
            "without_errors": clients_without_errors_count
        },
        "reconciliation": {
            "total": total_reconciliations,
            "matched": matched_total,
            "errors": total_errors,
            "success_percentage": round(
                (matched_total / total_reconciliations) * 100,
                2
            ) if total_reconciliations > 0 else 0
        },
        "movements": {
            "total": total_movements
        },
        "status_summary": status_summary
    }