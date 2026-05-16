import pandas as pd

def read_financial_file(file_path: str):
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Formato no soportado")

    df.columns = [str(col).lower().strip() for col in df.columns]
    return df
