import math
from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation

import pandas as pd


def normalize_text(value):
    if pd.isna(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    return text


def normalize_reference(value):
    if pd.isna(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    text = text.replace(",", "").strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text


def normalize_decimal(value):
    if pd.isna(value) or value == "":
        return None

    try:
        text = str(value).strip()

        if text == "":
            return None

        text = text.replace(",", "")
        text = text.replace(" ", "")

        if text in {"-", "+", "."}:
            return None

        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def normalize_date(value):
    if pd.isna(value) or value == "":
        return None

    try:
        return pd.to_datetime(value, dayfirst=True).to_pydatetime()
    except Exception:
        return None


def normalize_bank_datetime(row):
    fecha = get_value(row, "fecha", "date")
    hora = get_value(row, "hora")

    if fecha is None:
        return None

    if hora is not None and not pd.isna(hora):
        value = f"{fecha} {hora}"
    else:
        value = fecha

    return normalize_date(value)


def make_json_serializable(value):
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def clean_raw_data(row) -> dict:
    raw_data = row.where(pd.notnull(row), None).to_dict()

    cleaned = {}

    for key, value in raw_data.items():
        if str(key).startswith("ignore_"):
            continue

        cleaned[key] = make_json_serializable(value)

    return cleaned


def get_value(row, *possible_columns):
    for column in possible_columns:
        if column in row and not pd.isna(row[column]):
            return row[column]

    return None


def is_valid_transaction(item: dict) -> bool:
    has_reference = item.get("reference") is not None
    has_crypto_amount = item.get("amount") is not None
    has_fiat_amount = item.get("fiat_amount") is not None

    return has_reference and (has_crypto_amount or has_fiat_amount)


def normalize_sheet(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    sheet_key = sheet_name.strip().lower()

    if "extracto" in sheet_key and "pago" in sheet_key:
        return normalize_extracto_pagos(upload_id, sheet_name, df)

    if "extracto" in sheet_key and "cobro" in sheet_key:
        return normalize_extracto_cobros(upload_id, sheet_name, df)

    if "deposit" in sheet_key or "depósito" in sheet_key or "deposito" in sheet_key:
        return normalize_depositos(upload_id, sheet_name, df)

    if "retiro" in sheet_key:
        return normalize_retiros(upload_id, sheet_name, df)

    if "pago" in sheet_key and "qr" in sheet_key:
        return normalize_pago_qr(upload_id, sheet_name, df)

    if "cobro" in sheet_key and "qr" in sheet_key:
        return normalize_cobro_qr(upload_id, sheet_name, df)

    if "transfer" in sheet_key:
        return normalize_transfers(upload_id, sheet_name, df)

    return []


def normalize_depositos(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "crypto_operation",
            "service_type": "DEPOSITO",
            "client": normalize_text(get_value(row, "client", "account_name", "creado_por")),
            "date": normalize_date(get_value(row, "date", "local_time", "fecha_de_creacion", "createdat")),
            "asset": normalize_text(get_value(row, "currency", "product", "product_symbol", "product.symbol")) or "USDT",
            "amount": normalize_decimal(get_value(row, "amount", "crypto_quantity", "monto_intercambio")),
            "fiat_currency": None,
            "fiat_amount": None,
            "direction": "in",
            "reference": normalize_reference(get_value(row, "reference", "ticket_number", "transaccion_id")),
            "status": normalize_text(get_value(row, "status", "ticket_status", "estado")),
            "raw_data": clean_raw_data(row),
        }

        records.append(item)

    return records


def normalize_retiros(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "crypto_operation",
            "service_type": "RETIRO",
            "client": normalize_text(get_value(row, "client", "account_name", "creado_por")),
            "date": normalize_date(get_value(row, "date", "local_time", "fecha_de_creacion", "createdat")),
            "asset": normalize_text(get_value(row, "currency", "product", "product_symbol", "product.symbol")) or "USDT",
            "amount": normalize_decimal(
                get_value(
                    row,
                    "amount",
                    "crypto_quantity",
                    "monto_intercambio",
                    "importe_neto_sin_comision",
                    "monto_retiro_antes_comision",
                )
            ),
            "fiat_currency": None,
            "fiat_amount": None,
            "direction": "out",
            "reference": normalize_reference(get_value(row, "reference", "ticket_number", "transaccion_id")),
            "status": normalize_text(get_value(row, "status", "ticket_status", "estado")),
            "raw_data": clean_raw_data(row),
        }

        records.append(item)

    return records


def normalize_pago_qr(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "crypto_operation",
            "service_type": "PAGO_QR",
            "client": normalize_text(get_value(row, "client", "account_name", "creado_por")),
            "date": normalize_date(get_value(row, "date", "fecha_de_creacion", "fecha")),
            "asset": "USDT",
            "amount": normalize_decimal(get_value(row, "monto_intercambio", "amount", "crypto_quantity")),
            "fiat_currency": "BOB",
            "fiat_amount": normalize_decimal(get_value(row, "monto_pagado", "importe_en_bolivianos", "monto")),
            "direction": "out",
            "reference": normalize_reference(
                get_value(row, "reference", "codigo_de_transaccion", "transaccion_id")
            ),
            "status": normalize_text(get_value(row, "status", "estado")),
            "raw_data": clean_raw_data(row),
        }

        records.append(item)

    return records


def normalize_cobro_qr(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "crypto_operation",
            "service_type": "COBRO_QR",
            "client": normalize_text(get_value(row, "client", "account_name", "creado_por")),
            "date": normalize_date(get_value(row, "date", "fecha_de_creacion", "fecha")),
            "asset": "USDT",
            "amount": normalize_decimal(get_value(row, "monto_intercambio", "amount", "crypto_quantity")),
            "fiat_currency": "BOB",
            "fiat_amount": normalize_decimal(get_value(row, "monto_pagado", "importe_en_bolivianos", "monto")),
            "direction": "in",
            "reference": normalize_reference(
                get_value(row, "reference", "codigo_de_transaccion", "transaccion_id")
            ),
            "status": normalize_text(get_value(row, "status", "estado")),
            "raw_data": clean_raw_data(row),
        }

        records.append(item)

    return records


def normalize_transfers(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        sender = normalize_text(get_value(row, "senderaccount_alias", "senderaccount.alias", "client"))
        receiver = normalize_text(get_value(row, "receiveraccount_alias", "receiveraccount.alias"))

        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "internal_transfer",
            "service_type": "TRANSFER",
            "client": sender,
            "date": normalize_date(get_value(row, "date", "createdat", "fecha_de_creacion")),
            "asset": normalize_text(get_value(row, "currency", "product_symbol", "product.symbol")) or "USDT",
            "amount": normalize_decimal(get_value(row, "amount", "crypto_quantity")),
            "fiat_currency": None,
            "fiat_amount": None,
            "direction": "internal",
            "reference": normalize_reference(get_value(row, "reference", "transfernumber", "transfer_number")),
            "status": normalize_text(get_value(row, "status", "estado")),
            "raw_data": {
                **clean_raw_data(row),
                "normalized_sender": sender,
                "normalized_receiver": receiver,
            },
        }

        records.append(item)

    return records


def normalize_extracto_pagos(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        reference = normalize_reference(
            get_value(
                row,
                "reference",
                "codigo_de_transaccion",
                "transaccion_id",
                "nro_transaccion",
                "numero_transaccion",
                "id_transaccion",
            )
        )

        fiat_amount = normalize_decimal(
            get_value(
                row,
                "amount",
                "importe_en_bolivianos",
                "monto",
                "importe",
                "debito",
                "debe",
                "valor",
                "monto_bs",
                "monto_bob",
            )
        )

        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "bank_statement",
            "service_type": "EXTRACTO_PAGOS",
            "client": normalize_text(get_value(row, "client", "descripcion", "detalle", "glosa", "concepto")),
            "date": normalize_bank_datetime(row),
            "asset": None,
            "amount": None,
            "fiat_currency": "BOB",
            "fiat_amount": fiat_amount,
            "direction": "bank_out",
            "reference": reference,
            "status": normalize_text(get_value(row, "status", "estado")),
            "raw_data": clean_raw_data(row),
        }

        records.append(item)

    return records


def normalize_extracto_cobros(upload_id: int, sheet_name: str, df: pd.DataFrame) -> list[dict]:
    records = []

    for _, row in df.iterrows():
        reference = normalize_reference(
            get_value(
                row,
                "reference",
                "codigo_de_transaccion",
                "transaccion_id",
                "nro_transaccion",
                "numero_transaccion",
                "id_transaccion",
            )
        )

        fiat_amount = normalize_decimal(
            get_value(
                row,
                "amount",
                "importe_en_bolivianos",
                "monto",
                "importe",
                "credito",
                "haber",
                "valor",
                "monto_bs",
                "monto_bob",
            )
        )

        item = {
            "upload_id": upload_id,
            "sheet_name": sheet_name,
            "source_type": "bank_statement",
            "service_type": "EXTRACTO_COBROS",
            "client": normalize_text(get_value(row, "client", "descripcion", "detalle", "glosa", "concepto")),
            "date": normalize_bank_datetime(row),
            "asset": None,
            "amount": None,
            "fiat_currency": "BOB",
            "fiat_amount": fiat_amount,
            "direction": "bank_in",
            "reference": reference,
            "status": normalize_text(get_value(row, "status", "estado")),
            "raw_data": clean_raw_data(row),
        }

        records.append(item)

    return records


def normalize_workbook(upload_id: int, valid_sheets: dict[str, pd.DataFrame]) -> list[dict]:
    normalized_transactions = []

    for sheet_name, df in valid_sheets.items():
        sheet_transactions = normalize_sheet(
            upload_id=upload_id,
            sheet_name=sheet_name,
            df=df,
        )

        valid_transactions = [
            item for item in sheet_transactions
            if is_valid_transaction(item)
        ]

        normalized_transactions.extend(valid_transactions)

    return normalized_transactions