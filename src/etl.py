import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = {"date", "amount"}


def load_sales_csv(path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"sales data not found: {path}")

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise KeyError(next(iter(missing)))

    df["date"] = pd.to_datetime(df["date"])
    return df
