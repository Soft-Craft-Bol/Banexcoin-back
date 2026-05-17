from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_
from math import ceil

from app.core.database import get_db
from app.models.upload import Upload
from app.models.reconciliation import Reconciliation
from app.models.transaction import Transaction
from app.repositories.reconciliation_repository import (
    bulk_create_reconciliations,
    delete_reconciliations_by_upload,
    get_reconciliations,
)
from app.services.reconciliation_service import run_reconciliation


router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


def build_paginated_response(
    content: list,
    page: int,
    size: int,
    total_elements: int,
    offset: int,
    sorted_value: bool = True,
):
    total_pages = ceil(total_elements / size) if total_elements else 0

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
            "sorted": sorted_value,
            "unsorted": not sorted_value,
            "empty": False,
        },
    }


def paginate_query(query, page: int, size: int):
    total_elements = query.order_by(None).count()
    offset = page * size

    rows = query.offset(offset).limit(size).all()

    return rows, total_elements, offset


def serialize_transaction(tx: Transaction, include_raw_data: bool = False):
    data = {
        "id": tx.id,
        "service_type": tx.service_type,
        "client": tx.client,
        "date": tx.date,
        "asset": tx.asset,
        "amount": tx.amount,
        "fiat_currency": tx.fiat_currency,
        "fiat_amount": tx.fiat_amount,
        "direction": tx.direction,
        "reference": tx.reference,
        "status": tx.status,
    }

    if include_raw_data:
        data["raw_data"] = tx.raw_data

    return data


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
            "amount_difference": len([
                item for item in results
                if item["status"] == "AMOUNT_DIFFERENCE"
            ]),
            "missing_in_bank": len([
                item for item in results
                if item["status"] == "MISSING_IN_BANK"
            ]),
            "missing_in_operation": len([
                item for item in results
                if item["status"] == "MISSING_IN_OPERATION"
            ]),
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
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = (
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
    )

    rows, total_elements, offset = paginate_query(query, page, size)

    content = [
        {
            "reconciliation_type": row.reconciliation_type,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

    return build_paginated_response(
        content=content,
        page=page,
        size=size,
        total_elements=total_elements,
        offset=offset,
    )


@router.get("/summary/by-client")
def reconciliation_summary_by_client(
    upload_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    client_expr = func.coalesce(
        OperationTx.client,
        BankTx.client,
        "SIN_CLIENTE"
    )

    query = (
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
        .order_by(
            client_expr,
            Reconciliation.reconciliation_type,
            Reconciliation.status
        )
    )

    rows, total_elements, offset = paginate_query(query, page, size)

    content = [
        {
            "client": row.client,
            "reconciliation_type": row.reconciliation_type,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

    return build_paginated_response(
        content=content,
        page=page,
        size=size,
        total_elements=total_elements,
        offset=offset,
    )


@router.get("/client/{client_name}/details")
def reconciliation_client_details(
    client_name: str,
    upload_id: int,
    status: str | None = None,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=500),
    include_raw_data: bool = False,
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
        .order_by(Reconciliation.created_at.desc())
    )

    if status:
        query = query.filter(Reconciliation.status == status)

    rows, total_elements, offset = paginate_query(query, page, size)

    content = [
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
            "operation_transaction": serialize_transaction(
                operation_tx,
                include_raw_data
            ) if operation_tx else None,
            "bank_transaction": serialize_transaction(
                bank_tx,
                include_raw_data
            ) if bank_tx else None,
        }
        for reconciliation, operation_tx, bank_tx in rows
    ]

    return build_paginated_response(
        content=content,
        page=page,
        size=size,
        total_elements=total_elements,
        offset=offset,
    )


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
        .order_by(
            Reconciliation.status,
            Reconciliation.reconciliation_type,
            Reconciliation.reference,
            Reconciliation.id,
        )
    )

    rows, total_elements, offset = paginate_query(base_query, page, size)

    content = [
        {
            "client": operation_tx.client
            if operation_tx
            else bank_tx.client
            if bank_tx
            else None,
            "reconciliation_id": reconciliation.id,
            "reconciliation_type": reconciliation.reconciliation_type,
            "status": reconciliation.status,
            "reference": reconciliation.reference,
            "operation_amount": reconciliation.operation_amount,
            "bank_amount": reconciliation.bank_amount,
            "difference": reconciliation.difference,
            "message": reconciliation.message,
            "operation_transaction": serialize_transaction(
                operation_tx,
                include_raw_data
            ) if operation_tx else None,
            "bank_transaction": serialize_transaction(
                bank_tx,
                include_raw_data
            ) if bank_tx else None,
        }
        for reconciliation, operation_tx, bank_tx in rows
    ]

    return build_paginated_response(
        content=content,
        page=page,
        size=size,
        total_elements=total_elements,
        offset=offset,
    )


@router.get("/errors/by-client")
def reconciliation_errors_by_client(
    upload_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db)
):
    OperationTx = aliased(Transaction)
    BankTx = aliased(Transaction)

    client_expr = func.coalesce(
        OperationTx.client,
        BankTx.client,
        "SIN_CLIENTE"
    )

    query = (
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
        .order_by(func.count(Reconciliation.id).desc())
    )

    rows, total_elements, offset = paginate_query(query, page, size)

    content = [
        {
            "client": row.client,
            "status": row.status,
            "total": row.total
        }
        for row in rows
    ]

    return build_paginated_response(
        content=content,
        page=page,
        size=size,
        total_elements=total_elements,
        offset=offset,
    )