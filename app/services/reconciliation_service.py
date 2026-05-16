from sqlalchemy.orm import Session
from sqlalchemy import func

from app.repositories.transaction_repository import get_transactions
from app.repositories.wallet_repository import get_wallet_by_id
from app.repositories.reconciliation_repository import (
    save_reconciliation,
    update_reconciliation,
)

from app.services.crypto_service import get_erc20_balance

from app.models.asset import Asset
from app.models.data_source import DataSource
from app.models.transaction import Transaction


def reconcile_transactions_with_wallet(
    db: Session,
    wallet_id: int,
    token: str = "usdt"
):
    wallet = get_wallet_by_id(db, wallet_id)

    if not wallet:
        raise ValueError("Wallet no encontrada")

    transactions = get_transactions(db)

    if not transactions:
        raise ValueError("No hay transacciones para conciliar")

    total_transactions = sum(
        tx.amount for tx in transactions
        if tx.currency.lower() == token.lower()
    )

    blockchain_balance = get_erc20_balance(
        wallet.address,
        token,
        wallet.network
    )

    wallet_total = blockchain_balance["balance"]
    difference = wallet_total - total_transactions

    if difference == 0:
        status = "matched"
        details = "Los saldos coinciden correctamente"
    else:
        status = "difference_found"
        details = f"Diferencia detectada de {difference} {token.upper()}"

    return save_reconciliation(
        db,
        {
            "wallet_id": wallet.id,
            "source_a": "database_transactions",
            "source_b": f"blockchain_{wallet.network}_{token}",
            "total_a": total_transactions,
            "total_b": wallet_total,
            "difference": difference,
            "status": status,
            "details": details,
        }
    )


def create_reconciliation_period(db: Session, data):
    if data.end_date < data.start_date:
        raise ValueError("La fecha final no puede ser menor que la fecha inicial")

    data_source = db.query(DataSource).filter(
        DataSource.id == data.data_source_id
    ).first()

    if not data_source:
        raise ValueError("Fuente o servicio no encontrado")

    asset = db.query(Asset).filter(
        Asset.id == data.asset_id
    ).first()

    if not asset:
        raise ValueError("Activo no encontrado")

    return save_reconciliation(
        db,
        {
            "wallet_id": None,
            "source_a": data_source.name,
            "source_b": "saldo_reportado",
            "total_a": 0,
            "total_b": 0,
            "difference": 0,
            "status": "Pendiente",
            "details": "Periodo de conciliación creado.",
            "start_date": data.start_date,
            "end_date": data.end_date,
            "period_type": data.period_type,
            "data_source_id": data.data_source_id,
            "asset_id": data.asset_id,
        }
    )


def register_initial_balance(db: Session, reconciliation, initial_balance: float):
    return update_reconciliation(
        db,
        reconciliation,
        {
            "initial_balance": initial_balance,
            "status": "Pendiente",
            "details": "Saldo inicial registrado.",
        }
    )


def register_reported_final_balance(
    db: Session,
    reconciliation,
    reported_final_balance: float
):
    return update_reconciliation(
        db,
        reconciliation,
        {
            "reported_final_balance": reported_final_balance,
            "total_b": reported_final_balance,
            "status": "Pendiente",
            "details": "Saldo final reportado registrado.",
        }
    )


def calculate_expected_balance(db: Session, reconciliation):
    if reconciliation.initial_balance is None:
        raise ValueError("Debe registrar el saldo inicial antes de calcular")

    data_source = db.query(DataSource).filter(
        DataSource.id == reconciliation.data_source_id
    ).first()

    if not data_source:
        raise ValueError("Fuente o servicio no encontrado")

    transactions = db.query(Transaction).filter(
        Transaction.source == data_source.name,
        Transaction.asset_id == reconciliation.asset_id,
        func.date(Transaction.created_at) >= reconciliation.start_date,
        func.date(Transaction.created_at) <= reconciliation.end_date,
    ).all()

    entradas = sum(tx.amount for tx in transactions if tx.amount > 0)
    salidas = abs(sum(tx.amount for tx in transactions if tx.amount < 0))

    expected_balance = reconciliation.initial_balance + entradas - salidas

    return update_reconciliation(
        db,
        reconciliation,
        {
            "total_a": expected_balance,
            "expected_balance": expected_balance,
            "details": (
                f"Saldo inicial: {reconciliation.initial_balance}. "
                f"Entradas: {entradas}. "
                f"Salidas: {salidas}. "
                f"Operaciones: {len(transactions)}."
            ),
        }
    )


def detect_difference(db: Session, reconciliation):
    if reconciliation.expected_balance is None:
        reconciliation = calculate_expected_balance(db, reconciliation)

    if reconciliation.reported_final_balance is None:
        return update_reconciliation(
            db,
            reconciliation,
            {
                "status": "Pendiente",
                "details": "Falta registrar saldo final reportado.",
            }
        )

    difference = abs(
        reconciliation.expected_balance -
        reconciliation.reported_final_balance
    )

    status = "Cuadrado" if difference == 0 else "Con diferencia"

    return update_reconciliation(
        db,
        reconciliation,
        {
            "difference": difference,
            "status": status,
            "details": (
                f"Saldo esperado: {reconciliation.expected_balance}. "
                f"Saldo reportado: {reconciliation.reported_final_balance}. "
                f"Diferencia: {difference}."
            ),
        }
    )


def get_reconciliation_operations(db: Session, reconciliation):
    data_source = db.query(DataSource).filter(
        DataSource.id == reconciliation.data_source_id
    ).first()

    if not data_source:
        raise ValueError("Fuente o servicio no encontrado")

    return db.query(Transaction).filter(
        Transaction.source == data_source.name,
        Transaction.asset_id == reconciliation.asset_id,
        func.date(Transaction.created_at) >= reconciliation.start_date,
        func.date(Transaction.created_at) <= reconciliation.end_date,
    ).all()