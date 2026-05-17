from fastapi import APIRouter, Depends
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
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)

    if upload_id:
        query = query.filter(Transaction.upload_id == upload_id)

    if service_type:
        query = query.filter(Transaction.service_type == service_type)

    if source_type:
        query = query.filter(Transaction.source_type == source_type)

    transactions = query.order_by(Transaction.date.desc()).limit(500).all()

    return transactions

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