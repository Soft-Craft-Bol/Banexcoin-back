from sqlalchemy.orm import Session

from app.repositories.transaction_repository import get_transactions
from app.repositories.wallet_repository import get_wallet_by_id
from app.repositories.reconciliation_repository import save_reconciliation

from app.services.crypto_service import get_erc20_balance


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

    reconciliation = save_reconciliation(
        db,
        {
            "wallet_id": wallet.id,
            "source_a": "database_transactions",
            "source_b": f"blockchain_{wallet.network}_{token}",
            "total_a": total_transactions,
            "total_b": wallet_total,
            "difference": difference,
            "status": status,
            "details": details
        }
    )

    return reconciliation