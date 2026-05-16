import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".xlsm")

COLUMN_ALIASES = {
    # montos
    "amount": "amount",
    "crypto quantity": "amount",
    "monto pagado": "amount",
    "monto intercambio": "amount",
    "importe en bolivianos": "amount",
    "importe neto sin comision": "amount",

    # moneda / activo
    "currency": "currency",
    "moneda": "currency",
    "product": "currency",
    "product.symbol": "currency",

    # referencia
    "reference": "reference",
    "ticket number": "reference",
    "transacción id": "reference",
    "transaccion id": "reference",
    "codigo de transacción": "reference",
    "codigo de transaccion": "reference",
    "transfernumber": "reference",

    # cliente
    "client": "client",
    "account name": "client",
    "creado por": "client",
    "senderaccount.alias": "client",
    "receiveraccount.alias": "client",

    # fecha
    "date": "date",
    "local time": "date",
    "local time ": "date",
    "fecha de creación": "date",
    "fecha de creacion": "date",
    "fecha de actualización": "date",
    "fecha de actualizacion": "date",
    "createdat": "date",
    "fecha": "date",

    # tipo / servicio
    "tipo de servicio": "service_type",
    "oms": "source",
    "oms.name": "source",
    "ticket status": "status",
    "estado": "status",
}

REQUIRED_COLUMNS = {"amount"}


def clean_column_name(column):
    return (
        str(column)
        .lower()
        .strip()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


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


def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    df = normalize_columns(df)
    validate_financial_columns(df, "CSV")

    return {
        "CSV": df
    }


def read_excel_file(file_path):
    sheets = pd.read_excel(file_path, sheet_name=None)
    valid_sheets = {}
    errors = {}

    for sheet_name, df in sheets.items():
        # Quita hojas vacías
        df = df.dropna(how="all")

        if df.empty:
            errors[sheet_name] = "Hoja vacía"
            continue

        df = normalize_columns(df)

        try:
            validate_financial_columns(df, sheet_name)
            valid_sheets[sheet_name] = df
        except ValueError as exc:
            errors[sheet_name] = str(exc)

    return valid_sheets, errors


def read_financial_file(file_path):
    lower_path = file_path.lower()

    if lower_path.endswith(".csv"):
        valid_sheets = read_csv_file(file_path)
        return valid_sheets, {}

    if lower_path.endswith((".xlsx", ".xls", ".xlsm")):
        return read_excel_file(file_path)

    raise ValueError("Formato no soportado. Solo CSV o Excel.")