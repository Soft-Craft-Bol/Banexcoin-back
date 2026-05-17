from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.reported_balance import ReportedBalance


def to_decimal(value):
    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def decimal_to_float(value: Decimal):
    return float(value.quantize(Decimal("0.00000001")))


def get_period_key(date, period: str):
    if date is None:
        return "SIN_FECHA"

    if period == "daily":
        return date.strftime("%Y-%m-%d")

    if period == "monthly":
        return date.strftime("%Y-%m")

    return "TOTAL"


def add_balance_row(
    balances: dict,
    period_key: str,
    client: str,
    asset: str,
    service_type: str,
    amount: Decimal,
):
    if not client:
        client = "SIN_CLIENTE"

    if not asset:
        asset = "USDT"

    key = (period_key, client, asset)

    if key not in balances:
        balances[key] = {
            "period": period_key,
            "client": client,
            "asset": asset,
            "depositos": Decimal("0"),
            "retiros": Decimal("0"),
            "pago_qr": Decimal("0"),
            "cobro_qr": Decimal("0"),
            "transfer_in": Decimal("0"),
            "transfer_out": Decimal("0"),
            "net_movement": Decimal("0"),
            "initial_balance": Decimal("0"),
            "expected_final_balance": Decimal("0"),
            "reported_balance": None,
            "difference": None,
            "balance_status": "NOT_COMPARED",
        }

    row = balances[key]

    if service_type == "DEPOSITO":
        row["depositos"] += amount
        row["net_movement"] += amount

    elif service_type == "RETIRO":
        row["retiros"] += amount
        row["net_movement"] -= amount

    elif service_type == "PAGO_QR":
        row["pago_qr"] += amount
        row["net_movement"] -= amount

    elif service_type == "COBRO_QR":
        row["cobro_qr"] += amount
        row["net_movement"] += amount

    elif service_type == "TRANSFER_IN":
        row["transfer_in"] += amount
        row["net_movement"] += amount

    elif service_type == "TRANSFER_OUT":
        row["transfer_out"] += amount
        row["net_movement"] -= amount


def get_initial_balance_map(
    db: Session,
    upload_id: int,
    period: str,
):
    rows = (
        db.query(ReportedBalance)
        .filter(ReportedBalance.upload_id == upload_id)
        .filter(ReportedBalance.balance_type == "initial")
        .all()
    )

    result = {}

    for item in rows:
        item_period = item.period or period or "TOTAL"
        client = item.client or "SIN_CLIENTE"
        asset = item.asset or "USDT"

        key = (item_period, client, asset)
        result[key] = to_decimal(item.initial_balance or item.reported_balance)

    return result


def get_reported_final_balance_map(
    db: Session,
    upload_id: int,
    period: str,
):
    rows = (
        db.query(ReportedBalance)
        .filter(ReportedBalance.upload_id == upload_id)
        .filter(ReportedBalance.balance_type == "reported_final")
        .all()
    )

    result = {}

    for item in rows:
        item_period = item.period or period or "TOTAL"
        client = item.client or "SIN_CLIENTE"
        asset = item.asset or "USDT"

        key = (item_period, client, asset)
        result[key] = to_decimal(item.reported_balance)

    return result


def apply_initial_and_reported_balances(
    balances: dict,
    initial_map: dict,
    reported_map: dict,
):
    all_keys = set(balances.keys()) | set(initial_map.keys()) | set(reported_map.keys())

    for key in all_keys:
        period_key, client, asset = key

        if key not in balances:
            balances[key] = {
                "period": period_key,
                "client": client,
                "asset": asset,
                "depositos": Decimal("0"),
                "retiros": Decimal("0"),
                "pago_qr": Decimal("0"),
                "cobro_qr": Decimal("0"),
                "transfer_in": Decimal("0"),
                "transfer_out": Decimal("0"),
                "net_movement": Decimal("0"),
                "initial_balance": Decimal("0"),
                "expected_final_balance": Decimal("0"),
                "reported_balance": None,
                "difference": None,
                "balance_status": "NOT_COMPARED",
            }

        row = balances[key]

        initial_balance = initial_map.get(key, Decimal("0"))
        reported_balance = reported_map.get(key)

        row["initial_balance"] = initial_balance
        row["expected_final_balance"] = initial_balance + row["net_movement"]
        row["reported_balance"] = reported_balance

        if reported_balance is None:
            row["difference"] = None
            row["balance_status"] = "NO_REPORTED_BALANCE"
        else:
            difference = row["expected_final_balance"] - reported_balance
            row["difference"] = difference

            if difference == Decimal("0"):
                row["balance_status"] = "MATCHED"
            else:
                row["balance_status"] = "DIFFERENCE"


def calculate_balances(
    db: Session,
    upload_id: int,
    period: str = "monthly",
    use_initial_balance: bool = True,
    compare_reported: bool = True,
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.upload_id == upload_id)
        .all()
    )

    balances = {}

    for tx in transactions:
        if tx.source_type == "bank_statement":
            continue

        period_key = get_period_key(tx.date, period)
        amount = to_decimal(tx.amount)
        asset = tx.asset or "USDT"

        if tx.service_type == "TRANSFER":
            raw_data = tx.raw_data or {}

            sender = raw_data.get("normalized_sender") or tx.client
            receiver = raw_data.get("normalized_receiver")

            add_balance_row(
                balances=balances,
                period_key=period_key,
                client=sender,
                asset=asset,
                service_type="TRANSFER_OUT",
                amount=amount,
            )

            add_balance_row(
                balances=balances,
                period_key=period_key,
                client=receiver,
                asset=asset,
                service_type="TRANSFER_IN",
                amount=amount,
            )

            continue

        add_balance_row(
            balances=balances,
            period_key=period_key,
            client=tx.client,
            asset=asset,
            service_type=tx.service_type,
            amount=amount,
        )

    initial_map = {}
    reported_map = {}

    if use_initial_balance:
        initial_map = get_initial_balance_map(
            db=db,
            upload_id=upload_id,
            period=period,
        )

    if compare_reported:
        reported_map = get_reported_final_balance_map(
            db=db,
            upload_id=upload_id,
            period=period,
        )

    apply_initial_and_reported_balances(
        balances=balances,
        initial_map=initial_map,
        reported_map=reported_map,
    )

    result = []

    for row in balances.values():
        result.append({
            "period": row["period"],
            "client": row["client"],
            "asset": row["asset"],
            "initial_balance": decimal_to_float(row["initial_balance"]),
            "depositos": decimal_to_float(row["depositos"]),
            "retiros": decimal_to_float(row["retiros"]),
            "pago_qr": decimal_to_float(row["pago_qr"]),
            "cobro_qr": decimal_to_float(row["cobro_qr"]),
            "transfer_in": decimal_to_float(row["transfer_in"]),
            "transfer_out": decimal_to_float(row["transfer_out"]),
            "net_movement": decimal_to_float(row["net_movement"]),
            "expected_final_balance": decimal_to_float(row["expected_final_balance"]),
            "reported_balance": decimal_to_float(row["reported_balance"]) if row["reported_balance"] is not None else None,
            "difference": decimal_to_float(row["difference"]) if row["difference"] is not None else None,
            "balance_status": row["balance_status"],
        })

    return sorted(
        result,
        key=lambda item: (item["period"], item["client"], item["asset"])
    )


def calculate_balance_summary(
    balances: list[dict],
):
    total_clients = len({item["client"] for item in balances})
    total_rows = len(balances)

    matched = len([item for item in balances if item["balance_status"] == "MATCHED"])
    differences = len([item for item in balances if item["balance_status"] == "DIFFERENCE"])
    no_reported = len([item for item in balances if item["balance_status"] == "NO_REPORTED_BALANCE"])

    total_net_movement = sum(Decimal(str(item["net_movement"])) for item in balances)
    total_expected_final = sum(Decimal(str(item["expected_final_balance"])) for item in balances)

    return {
        "total_rows": total_rows,
        "total_clients": total_clients,
        "matched": matched,
        "differences": differences,
        "no_reported_balance": no_reported,
        "total_net_movement": decimal_to_float(total_net_movement),
        "total_expected_final_balance": decimal_to_float(total_expected_final),
    }