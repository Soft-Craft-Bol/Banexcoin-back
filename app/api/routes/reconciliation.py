from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.reconciliation import (
    ReconciliationCreate,
    ReconciliationResponse,
    ReconciliationPeriodCreate,
    InitialBalanceUpdate,
    ReportedFinalBalanceUpdate,
)

from app.repositories.reconciliation_repository import (
    get_reconciliations,
    get_reconciliation_by_id,
)

from app.services.reconciliation_service import (
    reconcile_transactions_with_wallet,
    create_reconciliation_period,
    register_initial_balance,
    register_reported_final_balance,
    calculate_expected_balance,
    detect_difference,
    get_reconciliation_operations,
)

router = APIRouter(
    prefix="/reconciliation",
    tags=["Reconciliation"]
)


@router.post("/wallet/{wallet_id}", response_model=ReconciliationResponse)
def reconcile_wallet(
    wallet_id: int,
    data: ReconciliationCreate,
    db: Session = Depends(get_db)
):
    try:
        return reconcile_transactions_with_wallet(
            db,
            wallet_id,
            data.token
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/", response_model=list[ReconciliationResponse])
def list_reconciliations(db: Session = Depends(get_db)):
    return get_reconciliations(db)


@router.get("/{reconciliation_id}", response_model=ReconciliationResponse)
def get_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(get_db)
):
    reconciliation = get_reconciliation_by_id(db, reconciliation_id)

    if not reconciliation:
        raise HTTPException(
            status_code=404,
            detail="Conciliación no encontrada"
        )

    return reconciliation


# ===== EPICA 5 =====

def get_reconciliation_or_404(db: Session, reconciliation_id: int):
    reconciliation = get_reconciliation_by_id(db, reconciliation_id)

    if not reconciliation:
        raise HTTPException(
            status_code=404,
            detail="Conciliación no encontrada"
        )

    return reconciliation


@router.post("/periods", response_model=ReconciliationResponse)
def create_period(
    data: ReconciliationPeriodCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_reconciliation_period(db, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.patch("/{reconciliation_id}/initial-balance", response_model=ReconciliationResponse)
def set_initial_balance(
    reconciliation_id: int,
    data: InitialBalanceUpdate,
    db: Session = Depends(get_db)
):
    reconciliation = get_reconciliation_or_404(db, reconciliation_id)

    return register_initial_balance(
        db,
        reconciliation,
        data.initial_balance
    )


@router.patch("/{reconciliation_id}/reported-final-balance", response_model=ReconciliationResponse)
def set_reported_final_balance(
    reconciliation_id: int,
    data: ReportedFinalBalanceUpdate,
    db: Session = Depends(get_db)
):
    reconciliation = get_reconciliation_or_404(db, reconciliation_id)

    return register_reported_final_balance(
        db,
        reconciliation,
        data.reported_final_balance
    )


@router.post("/{reconciliation_id}/calculate", response_model=ReconciliationResponse)
def calculate_balance(
    reconciliation_id: int,
    db: Session = Depends(get_db)
):
    try:
        reconciliation = get_reconciliation_or_404(db, reconciliation_id)
        return calculate_expected_balance(db, reconciliation)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{reconciliation_id}/detect-difference", response_model=ReconciliationResponse)
def detect_reconciliation_difference(
    reconciliation_id: int,
    db: Session = Depends(get_db)
):
    try:
        reconciliation = get_reconciliation_or_404(db, reconciliation_id)
        return detect_difference(db, reconciliation)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/{reconciliation_id}/operations")
def list_reconciliation_operations(
    reconciliation_id: int,
    db: Session = Depends(get_db)
):
    try:
        reconciliation = get_reconciliation_or_404(db, reconciliation_id)
        return get_reconciliation_operations(db, reconciliation)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))