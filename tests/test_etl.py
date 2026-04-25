import pytest
import pandas as pd
from src.etl import load_sales_csv


def test_load_sales_csv_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="sales data not found"):
        load_sales_csv(tmp_path / "nonexistent.csv")


def test_load_sales_csv_missing_required_column(tmp_path):
    bad_csv = tmp_path / "sales.csv"
    bad_csv.write_text("wrong_col,amount\n1,100\n")
    with pytest.raises(KeyError):
        load_sales_csv(bad_csv)


def test_load_sales_csv_parses_dates(tmp_path):
    csv = tmp_path / "sales.csv"
    csv.write_text("date,amount\n2024-01-15,500\n")
    df = load_sales_csv(csv)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_load_sales_csv_returns_dataframe(tmp_path):
    csv = tmp_path / "sales.csv"
    csv.write_text("date,amount,region\n2024-01-15,500,West\n2024-02-10,300,East\n")
    df = load_sales_csv(csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "amount" in df.columns
