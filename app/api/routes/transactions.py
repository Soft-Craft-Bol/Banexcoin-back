from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.repositories.transaction_repository import (
    create_transaction,
    get_transactions
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse)
def create_transaction_endpoint(
    data: TransactionCreate,
    db: Session = Depends(get_db)
):
    return create_transaction(
        db,
        {
            "source": data.source,
            "tx_type": data.tx_type,
            "reference": data.reference,
            "amount": data.amount,
            "currency": data.currency,
        }
    )


@router.get("/", response_model=list[TransactionResponse])
def list_transactions(
    db: Session = Depends(get_db)
):
    return get_transactions(db)