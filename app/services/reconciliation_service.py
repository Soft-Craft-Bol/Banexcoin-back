from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def to_decimal(value):
    if value is None:
        return None

    return Decimal(str(value)).quantize(Decimal("0.01"))


def build_index_by_reference(transactions):
    index = {}

    for tx in transactions:
        if not tx.reference:
            continue

        reference = str(tx.reference).strip()

        if reference.endswith(".0"):
            reference = reference[:-2]

        index[reference] = tx

    return index


def compare_transaction_groups(
    upload_id: int,
    operation_transactions: list[Transaction],
    bank_transactions: list[Transaction],
    reconciliation_type: str
) -> list[dict]:
    results = []

    operation_index = build_index_by_reference(operation_transactions)
    bank_index = build_index_by_reference(bank_transactions)

    all_references = set(operation_index.keys()) | set(bank_index.keys())

    for reference in all_references:
        operation_tx = operation_index.get(reference)
        bank_tx = bank_index.get(reference)

        if operation_tx and bank_tx:
            operation_amount = to_decimal(operation_tx.fiat_amount)
            bank_amount = to_decimal(bank_tx.fiat_amount)

            difference = None

            if operation_amount is not None and bank_amount is not None:
                difference = operation_amount - abs(bank_amount)

            if difference == Decimal("0.00"):
                status = "MATCHED"
                message = "Operación conciliada correctamente"
            else:
                status = "AMOUNT_DIFFERENCE"
                message = "La referencia existe en ambos lados, pero el monto no coincide"

            results.append({
                "upload_id": upload_id,
                "operation_transaction_id": operation_tx.id,
                "bank_transaction_id": bank_tx.id,
                "reconciliation_type": reconciliation_type,
                "reference": reference,
                "operation_amount": operation_amount,
                "bank_amount": bank_amount,
                "difference": difference,
                "status": status,
                "message": message,
            })

        elif operation_tx and not bank_tx:
            results.append({
                "upload_id": upload_id,
                "operation_transaction_id": operation_tx.id,
                "bank_transaction_id": None,
                "reconciliation_type": reconciliation_type,
                "reference": reference,
                "operation_amount": to_decimal(operation_tx.fiat_amount),
                "bank_amount": None,
                "difference": to_decimal(operation_tx.fiat_amount),
                "status": "MISSING_IN_BANK",
                "message": "La operación existe en Banexcoin, pero no existe en el extracto bancario",
            })

        elif bank_tx and not operation_tx:
            results.append({
                "upload_id": upload_id,
                "operation_transaction_id": None,
                "bank_transaction_id": bank_tx.id,
                "reconciliation_type": reconciliation_type,
                "reference": reference,
                "operation_amount": None,
                "bank_amount": to_decimal(bank_tx.fiat_amount),
                "difference": to_decimal(bank_tx.fiat_amount),
                "status": "MISSING_IN_OPERATION",
                "message": "El movimiento existe en el banco, pero no existe en Banexcoin",
            })

    return results


def run_reconciliation(db: Session, upload_id: int) -> list[dict]:
    transactions = db.query(Transaction).filter(
        Transaction.upload_id == upload_id
    ).all()

    pago_qr = [
        tx for tx in transactions
        if tx.service_type == "PAGO_QR"
    ]

    extracto_pagos = [
        tx for tx in transactions
        if tx.service_type == "EXTRACTO_PAGOS"
    ]

    cobro_qr = [
        tx for tx in transactions
        if tx.service_type == "COBRO_QR"
    ]

    extracto_cobros = [
        tx for tx in transactions
        if tx.service_type == "EXTRACTO_COBROS"
    ]

    results = []

    results.extend(
        compare_transaction_groups(
            upload_id=upload_id,
            operation_transactions=pago_qr,
            bank_transactions=extracto_pagos,
            reconciliation_type="PAGO_QR_VS_EXTRACTO_PAGOS"
        )
    )

    results.extend(
        compare_transaction_groups(
            upload_id=upload_id,
            operation_transactions=cobro_qr,
            bank_transactions=extracto_cobros,
            reconciliation_type="COBRO_QR_VS_EXTRACTO_COBROS"
        )
    )

    return results