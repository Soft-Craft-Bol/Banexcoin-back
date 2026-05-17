import math
import unicodedata

import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".xlsm")

COLUMN_ALIASES = {
    "amount": "amount",
    "crypto quantity": "amount",
    "monto pagado": "amount",
    "monto intercambio": "exchange_amount",
    "importe en bolivianos": "amount",
    "importe neto sin comision": "net_amount",
    "monto de retiro antes de comision": "withdrawal_amount",
    "debe": "debit",
    "haber": "credit",
    "currency": "currency",
    "moneda": "currency",
    "product": "currency",
    "product.symbol": "currency",
    "reference": "reference",
    "ticket number": "reference",
    "transaccion id": "reference",
    "codigo de transaccion": "reference",
    "transfernumber": "reference",
    "client": "client",
    "account name": "client",
    "creado por": "client",
    "senderaccount.alias": "client",
    "receiveraccount.alias": "client",
    "date": "date",
    "local time": "date",
    "fecha de creacion": "date",
    "fecha de actualizacion": "date",
    "createdat": "date",
    "fecha": "date",
    "tipo de servicio": "service_type",
    "oms": "source",
    "oms.name": "source",
    "ticket status": "status",
    "estado": "status",
}

REQUIRED_COLUMNS = {"amount"}


def clean_column_name(column):
    text = str(column).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())


def normalize_columns(df):
    rename_map = {}

    for column in df.columns:
        clean = clean_column_name(column)
        rename_map[column] = COLUMN_ALIASES.get(clean, clean.replace(" ", "_"))

    return df.rename(columns=rename_map)


def validate_financial_columns(df, sheet_name="archivo"):
    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"La hoja '{sheet_name}' no tiene columnas requeridas: {', '.join(missing)}"
        )


def normalize_dataframe(df, sheet_name, default_source="manual"):
    df = df.dropna(how="all")

    if df.empty:
        raise ValueError("Hoja vacia")

    df = normalize_columns(df)
    validate_financial_columns(df, sheet_name)

    df["sheet_name"] = sheet_name

    if "source" not in df.columns:
        df["source"] = default_source

    if "currency" not in df.columns:
        df["currency"] = "USD"

    return df


def read_csv_file(file_path, default_source="manual"):
    df = pd.read_csv(file_path)
    return {"CSV": normalize_dataframe(df, "CSV", default_source)}


def read_excel_file(file_path, default_source="manual"):
    sheets = pd.read_excel(file_path, sheet_name=None)
    valid_sheets = {}
    errors = {}

    for sheet_name, df in sheets.items():
        try:
            valid_sheets[sheet_name] = normalize_dataframe(df, sheet_name, default_source)
        except Exception as exc:
            errors[sheet_name] = str(exc)

    return valid_sheets, errors


def read_financial_file(file_path, default_source="manual"):
    lower_path = file_path.lower()

    if lower_path.endswith(".csv"):
        return read_csv_file(file_path, default_source), {}

    if lower_path.endswith((".xlsx", ".xls", ".xlsm")):
        return read_excel_file(file_path, default_source)

    raise ValueError("Formato no soportado. Solo CSV o Excel.")


def dataframe_to_transactions(valid_sheets, default_source="manual"):
    transactions = []

    for sheet_name, df in valid_sheets.items():
        for index, row in df.iterrows():
            amount = row.get("amount")

            if pd.isna(amount):
                continue

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                raise ValueError(f"Monto invalido en hoja '{sheet_name}', fila {index + 2}")

            if math.isnan(amount):
                continue

            transactions.append(
                {
                    "source": str(row.get("source") or default_source),
                    "tx_type": str(row.get("service_type") or sheet_name),
                    "reference": None if pd.isna(row.get("reference")) else str(row.get("reference")),
                    "amount": amount,
                    "currency": str(row.get("currency") or "USD"),
                    "status": "processed",
                }
            )

    return transactions
 