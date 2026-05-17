import re
import unicodedata

import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".xlsm")


COLUMN_ALIASES = {
    # montos cripto
    "amount": "amount",
    "crypto quantity": "crypto_quantity",
    "crypto_quantity": "crypto_quantity",
    "monto intercambio": "monto_intercambio",
    "monto_intercambio": "monto_intercambio",
    "importe neto sin comision": "importe_neto_sin_comision",
    "importe neto sin comisión": "importe_neto_sin_comision",
    "monto de retiro antes de comision": "monto_retiro_antes_comision",
    "monto de retiro antes de comisión": "monto_retiro_antes_comision",

    # montos fiat / banco
    "monto pagado": "monto_pagado",
    "monto_pagado": "monto_pagado",
    "importe en bolivianos": "importe_en_bolivianos",
    "importe_en_bolivianos": "importe_en_bolivianos",
    "monto": "monto",
    "importe": "importe",
    "debito": "debito",
    "débito": "debito",
    "credito": "credito",
    "crédito": "credito",
    "debe": "debe",
    "haber": "haber",
    "valor": "valor",
    "monto bs": "monto_bs",
    "monto bob": "monto_bob",

    # moneda / activo
    "currency": "currency",
    "moneda": "currency",
    "product": "product",
    "product.symbol": "product_symbol",
    "product symbol": "product_symbol",

    # referencias
    "reference": "reference",
    "ticket number": "ticket_number",
    "ticket_number": "ticket_number",
    "transacción id": "transaccion_id",
    "transaccion id": "transaccion_id",
    "codigo de transacción": "codigo_de_transaccion",
    "codigo de transaccion": "codigo_de_transaccion",
    "código de transacción": "codigo_de_transaccion",
    "codigo transacción": "codigo_de_transaccion",
    "codigo transaccion": "codigo_de_transaccion",
    "codigo_de_transaccion": "codigo_de_transaccion",
    "nro transaccion": "nro_transaccion",
    "nro. transaccion": "nro_transaccion",
    "numero transaccion": "numero_transaccion",
    "número transacción": "numero_transaccion",
    "id transaccion": "id_transaccion",
    "transfernumber": "transfernumber",
    "transfer number": "transfer_number",

    # cliente
    "client": "client",
    "account name": "account_name",
    "account_name": "account_name",
    "creado por": "creado_por",
    "creado_por": "creado_por",
    "senderaccount.alias": "senderaccount_alias",
    "receiveraccount.alias": "receiveraccount_alias",

    # fecha / hora
    "date": "date",
    "local time": "local_time",
    "local time ": "local_time",
    "fecha de creación": "fecha_de_creacion",
    "fecha de creacion": "fecha_de_creacion",
    "fecha de actualización": "fecha_de_actualizacion",
    "fecha de actualizacion": "fecha_de_actualizacion",
    "fecha y hora": "fecha_y_hora",
    "createdat": "createdat",
    "fecha": "fecha",
    "hora": "hora",

    # estado / servicio
    "tipo de servicio": "service_type",
    "oms": "source",
    "oms.name": "source",
    "ticket status": "ticket_status",
    "estado": "estado",

    # banco
    "descripcion": "descripcion",
    "descripción": "descripcion",
    "detalle": "detalle",
    "glosa": "glosa",
    "concepto": "concepto",
}


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def clean_column_name(column):
    text = str(column)

    text = text.replace("\xa0", " ")
    text = text.replace("\t", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    text = text.lower().strip()
    text = remove_accents(text)
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_columns(df):
    rename_map = {}

    for column in df.columns:
        clean = clean_column_name(column)
        normalized = clean.replace(" ", "_")
        final_name = COLUMN_ALIASES.get(clean, normalized)

        rename_map[column] = final_name

    return df.rename(columns=rename_map)


def is_extract_sheet(sheet_name: str) -> bool:
    clean_name = sheet_name.strip().upper()
    return clean_name in {"EXTRACTO DE PAGOS", "EXTRACTO DE COBROS"}


def promote_first_row_to_header_for_extract(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    if not is_extract_sheet(sheet_name):
        return df

    if df.empty:
        return df

    original_columns = [str(col) for col in df.columns]
    has_unnamed_columns = any(col.lower().startswith("unnamed") for col in original_columns)

    if not has_unnamed_columns:
        return df

    first_row_values = df.iloc[0].tolist()
    first_row_text = " ".join([str(value).lower() for value in first_row_values if not pd.isna(value)])

    looks_like_header = (
        "fecha" in first_row_text
        and "hora" in first_row_text
        and ("codigo" in first_row_text or "transaccion" in first_row_text)
        and "importe" in first_row_text
    )

    if not looks_like_header:
        return df

    new_columns = []

    for i, value in enumerate(first_row_values):
        if pd.isna(value):
            new_columns.append(f"ignore_{i}")
        else:
            new_columns.append(str(value).strip())

    df = df.iloc[1:].copy()
    df.columns = new_columns

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    return df


def sheet_has_useful_data(df):
    possible_amount_columns = {
        "amount",
        "crypto_quantity",
        "monto_intercambio",
        "monto_pagado",
        "importe_en_bolivianos",
        "importe_neto_sin_comision",
        "monto_retiro_antes_comision",
        "monto",
        "importe",
        "debito",
        "credito",
        "debe",
        "haber",
        "valor",
        "monto_bs",
        "monto_bob",
    }

    possible_reference_columns = {
        "reference",
        "ticket_number",
        "transaccion_id",
        "codigo_de_transaccion",
        "transfernumber",
        "transfer_number",
        "nro_transaccion",
        "numero_transaccion",
        "id_transaccion",
    }

    columns = set(df.columns)

    has_amount = bool(columns & possible_amount_columns)
    has_reference = bool(columns & possible_reference_columns)

    return has_amount or has_reference


def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df = normalize_columns(df)

    if not sheet_has_useful_data(df):
        raise ValueError("El CSV no tiene columnas financieras reconocibles")

    return {
        "CSV": df
    }


def read_excel_file(file_path):
    sheets = pd.read_excel(file_path, sheet_name=None)
    valid_sheets = {}
    errors = {}

    for sheet_name, df in sheets.items():
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")

        if df.empty:
            errors[sheet_name] = "Hoja vacía"
            continue

        df = promote_first_row_to_header_for_extract(df, sheet_name)

        if df.empty:
            errors[sheet_name] = "Hoja vacía después de promover encabezado"
            continue

        df = normalize_columns(df)

        if not sheet_has_useful_data(df):
            errors[sheet_name] = "No tiene columnas financieras reconocibles"
            continue

        valid_sheets[sheet_name] = df

    return valid_sheets, errors


def read_financial_file(file_path):
    lower_path = file_path.lower()

    if lower_path.endswith(".csv"):
        valid_sheets = read_csv_file(file_path)
        return valid_sheets, {}

    if lower_path.endswith((".xlsx", ".xls", ".xlsm")):
        return read_excel_file(file_path)

    raise ValueError("Formato no soportado. Solo CSV o Excel.")