# Test Coverage Analysis

## Current State

This repository (`deekseek2/deekseek2`) is a GitHub profile README and currently contains **no source code**. As a result:

- No test framework is configured
- No test files exist
- No CI/CD pipeline runs tests
- **Effective test coverage: 0%**

The sections below document a concrete roadmap for building good test coverage as data analysis scripts and projects are added to this profile.

---

## Priority Areas for Improvement

### 1. Data Processing Functions — High Priority

**Gap:** Any Python scripts performing aggregations, filters, or joins have zero test coverage. These are the highest-value targets because silent data errors compound downstream.

**What to test:**
- Input validation: empty DataFrames, `NaN`/`None` values, unexpected column types
- Transformation correctness: verify that aggregations, window functions, and reshapes produce expected output
- Edge cases: single-row input, all-identical values, overflow-prone calculations

**Example pattern:**
```python
# tests/test_data_processing.py
import pytest
import pandas as pd
from src.processing import compute_summary, clean_nulls

def test_compute_summary_empty_input():
    df = pd.DataFrame(columns=["revenue", "region"])
    result = compute_summary(df)
    assert result["total_revenue"] == 0
    assert result["row_count"] == 0

def test_clean_nulls_preserves_non_null_rows():
    df = pd.DataFrame({"value": [1, None, 3]})
    result = clean_nulls(df)
    assert len(result) == 2
    assert result["value"].isna().sum() == 0

def test_compute_summary_negative_values():
    df = pd.DataFrame({"revenue": [-100, 200, -50], "region": ["A", "A", "B"]})
    result = compute_summary(df)
    assert result["total_revenue"] == 50
```

---

### 2. ETL / Data Loading — High Priority

**Gap:** Scripts that read from CSV files, databases, or APIs have no tests for failure modes, which means they crash in production rather than giving useful errors.

**What to test:**
- File not found: should raise a clear error, not an unhandled `FileNotFoundError`
- Schema changes: missing or renamed columns must be detected early
- Encoding issues: non-UTF-8 source files should not silently corrupt data
- Type coercion: dates, numerics, and categoricals read correctly from CSV

**Example pattern:**
```python
# tests/test_etl.py
import pytest
from src.etl import load_sales_csv

def test_load_sales_csv_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="sales data not found"):
        load_sales_csv(tmp_path / "nonexistent.csv")

def test_load_sales_csv_missing_required_column(tmp_path):
    bad_csv = tmp_path / "sales.csv"
    bad_csv.write_text("wrong_col,amount\n1,100\n")
    with pytest.raises(KeyError, match="date"):
        load_sales_csv(bad_csv)

def test_load_sales_csv_parses_dates(tmp_path):
    csv = tmp_path / "sales.csv"
    csv.write_text("date,amount\n2024-01-15,500\n")
    df = load_sales_csv(csv)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
```

---

### 3. SQL Query Logic — Medium Priority

**Gap:** BI queries used in dashboards (GROUP BY, HAVING, window functions, multi-table JOINs) are not tested, so regressions go unnoticed when queries are modified.

**What to test:**
- Correctness of aggregations against known fixture data
- JOIN cardinality: does a query accidentally produce duplicate rows?
- Boundary conditions: HAVING filters, date range filters, NULL handling in aggregates

**Recommended approach:** Use DuckDB as an in-memory SQL engine for fast, dependency-free query tests.

```python
# tests/test_sql_queries.py
import duckdb
from pathlib import Path

def test_monthly_revenue_query_groups_correctly():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE sales (date DATE, amount DECIMAL, region VARCHAR);
        INSERT INTO sales VALUES
            ('2024-01-05', 100, 'West'),
            ('2024-01-20', 200, 'West'),
            ('2024-02-10', 150, 'East');
    """)
    query = Path("sql/monthly_revenue.sql").read_text()
    result = con.execute(query).df()
    assert len(result) == 2  # two months
    assert result.loc[result["month"] == "2024-01", "revenue"].iloc[0] == 300

def test_revenue_query_excludes_nulls():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE sales (date DATE, amount DECIMAL, region VARCHAR);
        INSERT INTO sales VALUES ('2024-01-01', NULL, 'West'), ('2024-01-01', 500, 'East');
    """)
    query = Path("sql/monthly_revenue.sql").read_text()
    result = con.execute(query).df()
    assert result["revenue"].iloc[0] == 500  # NULL excluded from SUM
```

---

### 4. Visualisation Helpers — Medium Priority

**Gap:** Chart-building code can fail silently — producing empty or misleading visuals if input data is malformed. No tests currently catch this.

**What to test:**
- Required columns exist before plotting (guard against silent empty charts)
- Output files are created at expected paths when saving figures
- Axis labels and titles are set (so exports are always labelled)

```python
# tests/test_visualisation.py
import pytest
import pandas as pd
from src.visualisation import plot_revenue_by_region

def test_plot_raises_on_missing_column():
    df = pd.DataFrame({"wrong_col": [1, 2, 3]})
    with pytest.raises(KeyError, match="revenue"):
        plot_revenue_by_region(df, output_path=None)

def test_plot_saves_file(tmp_path):
    df = pd.DataFrame({"region": ["A", "B"], "revenue": [300, 500]})
    out = tmp_path / "chart.png"
    plot_revenue_by_region(df, output_path=out)
    assert out.exists()
    assert out.stat().st_size > 0
```

---

### 5. End-to-End / Pipeline Integration — Lower Priority

**Gap:** No smoke test verifies that an entire pipeline (load → clean → transform → output) runs successfully end-to-end, even on a tiny sample.

**What to test:**
- Pipeline completes without error on a minimal fixture dataset
- Output schema matches expected column names and dtypes
- Output row count is deterministic for a given input

```python
# tests/test_pipeline_e2e.py
def test_full_pipeline_produces_expected_schema(tmp_path):
    # Minimal fixture: 5 rows, known output
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("date,amount,region\n2024-01-01,100,West\n")
    output_csv = tmp_path / "output.csv"

    run_pipeline(input_path=input_csv, output_path=output_csv)

    result = pd.read_csv(output_csv)
    assert set(result.columns) == {"month", "region", "total_revenue"}
    assert len(result) == 1
```

---

## Recommended Tooling Setup

Install once per project:
```
pytest              # test runner
pytest-cov          # line coverage reporting
pandas              # DataFrame fixtures
duckdb              # in-memory SQL testing (no server needed)
pytest-mock         # mocking file I/O and external API calls
```

### `pyproject.toml` configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
]
```

### Folder layout to target

```
project/
├── src/
│   ├── processing.py    # data transforms
│   ├── etl.py           # data loading
│   ├── visualisation.py # chart helpers
│   └── pipeline.py      # orchestration
├── sql/
│   └── monthly_revenue.sql
└── tests/
    ├── conftest.py          # shared fixtures
    ├── test_data_processing.py
    ├── test_etl.py
    ├── test_sql_queries.py
    ├── test_visualisation.py
    └── test_pipeline_e2e.py
```

**Coverage target: ≥ 80% line coverage on all `src/` modules before merging.**

---

## Summary

| Area | Current Coverage | Priority | Effort |
|------|-----------------|----------|--------|
| Data processing / transforms | 0% | High | Low–Medium |
| ETL / data loading | 0% | High | Low |
| SQL query logic | 0% | Medium | Medium |
| Visualisation helpers | 0% | Medium | Low |
| End-to-end pipeline | 0% | Lower | Medium–High |

Start with areas 1 and 2 — they catch the most impactful bugs with the least test-writing effort. SQL and visualisation tests can be added incrementally as queries and charts are built. End-to-end tests are best deferred until the pipeline shape stabilises.
