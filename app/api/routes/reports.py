from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.balance_service import calculate_balances, calculate_balance_summary
from app.utils.pagination import paginate_list


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/balances")
def get_balances_report(
    upload_id: int,
    period: str = "monthly",
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=200),
    client: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    if period not in {"daily", "monthly", "total"}:
        period = "monthly"

    balances = calculate_balances(
        db=db,
        upload_id=upload_id,
        period=period,
        use_initial_balance=True,
        compare_reported=True,
    )

    if client:
        balances = [
            item for item in balances
            if item["client"] == client
        ]

    if status:
        balances = [
            item for item in balances
            if item["balance_status"] == status
        ]

    return paginate_list(
        items=balances,
        page=page,
        size=size,
    )


@router.get("/balances/summary")
def get_balances_summary(
    upload_id: int,
    period: str = "monthly",
    db: Session = Depends(get_db)
):
    if period not in {"daily", "monthly", "total"}:
        period = "monthly"

    balances = calculate_balances(
        db=db,
        upload_id=upload_id,
        period=period,
        use_initial_balance=True,
        compare_reported=True,
    )

    return calculate_balance_summary(balances)


@router.get("/balances/errors")
def get_balance_errors(
    upload_id: int,
    period: str = "monthly",
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=200),
    client: str | None = None,
    db: Session = Depends(get_db)
):
    if period not in {"daily", "monthly", "total"}:
        period = "monthly"

    balances = calculate_balances(
        db=db,
        upload_id=upload_id,
        period=period,
        use_initial_balance=True,
        compare_reported=True,
    )

    errors = [
        item for item in balances
        if item["balance_status"] in {"DIFFERENCE", "NO_REPORTED_BALANCE"}
    ]

    if client:
        errors = [
            item for item in errors
            if item["client"] == client
        ]

    return paginate_list(
        items=errors,
        page=page,
        size=size,
    )


@router.get("/balances/client/{client_name}")
def get_client_balance_detail(
    client_name: str,
    upload_id: int,
    period: str = "monthly",
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db)
):
    if period not in {"daily", "monthly", "total"}:
        period = "monthly"

    balances = calculate_balances(
        db=db,
        upload_id=upload_id,
        period=period,
        use_initial_balance=True,
        compare_reported=True,
    )

    client_rows = [
        item for item in balances
        if item["client"] == client_name
    ]

    return paginate_list(
        items=client_rows,
        page=page,
        size=size,
    )


@router.get("/balances/no-initial")
def get_balances_without_initial_balance(
    upload_id: int,
    period: str = "monthly",
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db)
):
    if period not in {"daily", "monthly", "total"}:
        period = "monthly"

    balances = calculate_balances(
        db=db,
        upload_id=upload_id,
        period=period,
        use_initial_balance=False,
        compare_reported=False,
    )

    return paginate_list(
        items=balances,
        page=page,
        size=size,
    )