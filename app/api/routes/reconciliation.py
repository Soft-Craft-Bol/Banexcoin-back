from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.reconciliation import ReconciliationResponse

from app.services.reconciliation_service import reconcile_transactions_with_wallet

from app.repositories.reconciliation_repository import (
    get_reconciliations,
    get_reconciliation_by_id
)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/wallet/{wallet_id}", response_model=ReconciliationResponse)
def reconcile_wallet(
    wallet_id: int,
    token: str = Query(default="usdt"),
    db: Session = Depends(get_db)
):
    try:
        return reconcile_transactions_with_wallet(
            db=db,
            wallet_id=wallet_id,
            token=token
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


@router.get("/", response_model=list[ReconciliationResponse])
def list_reconciliations(
    db: Session = Depends(get_db)
):
    return get_reconciliations(db)


@router.get("/{reconciliation_id}", response_model=ReconciliationResponse)
def get_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(get_db)
):
    reconciliation = get_reconciliation_by_id(
        db,
        reconciliation_id
    )

    if not reconciliation:
        raise HTTPException(
            status_code=404,
            detail="Conciliación no encontrada"
        )

    return reconciliation