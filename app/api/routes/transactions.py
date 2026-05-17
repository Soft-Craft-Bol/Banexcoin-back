from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.transaction import Transaction

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/")
def list_transactions(
    upload_id: int | None = None,
    service_type: str | None = None,
    source_type: str | None = None,

    # PAGINACION
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=200),

    db: Session = Depends(get_db)
):
    query = db.query(Transaction)

    if upload_id:
        query = query.filter(Transaction.upload_id == upload_id)

    if service_type:
        query = query.filter(Transaction.service_type == service_type)

    if source_type:
        query = query.filter(Transaction.source_type == source_type)

    total_elements = query.count()

    total_pages = (
        ceil(total_elements / size)
        if total_elements > 0
        else 0
    )

    transactions = (
        query
        .order_by(Transaction.date.desc())
        .offset(page * size)
        .limit(size)
        .all()
    )

    return {
        "content": transactions,
        "page": page,
        "size": size,
        "totalElements": total_elements,
        "totalPages": total_pages,
        "numberOfElements": len(transactions),
        "first": page == 0,
        "last": page >= total_pages - 1 if total_pages > 0 else True,
        "empty": len(transactions) == 0
    }

@router.get("/summary/by-service")
def summary_by_service(
    upload_id: int,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(
            Transaction.service_type,
            Transaction.source_type,
            func.count(Transaction.id).label("total")
        )
        .filter(Transaction.upload_id == upload_id)
        .group_by(Transaction.service_type, Transaction.source_type)
        .order_by(Transaction.service_type)
        .all()
    )

    return [
        {
            "service_type": row.service_type,
            "source_type": row.source_type,
            "total": row.total
        }
        for row in rows
    ]

@router.get("/sample")
def sample_transactions(
    upload_id: int,
    service_type: str,
    db: Session = Depends(get_db)
):
    records = (
        db.query(Transaction)
        .filter(Transaction.upload_id == upload_id)
        .filter(Transaction.service_type == service_type)
        .limit(10)
        .all()
    )

    return [
        {
            "id": item.id,
            "service_type": item.service_type,
            "date": item.date,
            "reference": item.reference,
            "amount": item.amount,
            "fiat_amount": item.fiat_amount,
            "client": item.client,
            "raw_data": item.raw_data,
        }
        for item in records
    ]