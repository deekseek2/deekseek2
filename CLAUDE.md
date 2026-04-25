# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run all tests with coverage:**
```
pytest
```

**Run a single test file:**
```
pytest tests/test_etl.py
```

**Run a single test by name:**
```
pytest tests/test_etl.py::test_load_sales_csv_parses_dates
```

Coverage is enforced at ≥80% line coverage on `src/` — pytest will fail if it drops below.

## Architecture

This is an early-stage Python data analytics project. Source code lives in `src/`, tests in `tests/`.

**Current module:**
- `src/etl.py` — CSV ingestion. `load_sales_csv(path)` validates file existence, enforces required columns (`date`, `amount`), and parses dates into `datetime64`. Raises `FileNotFoundError` or `KeyError` on bad input rather than returning partial/silent failures.

**Planned layout (from TEST_COVERAGE.md):**
- `src/processing.py` — aggregations, filters, window transforms
- `src/visualisation.py` — chart helpers (guard required columns before plotting)
- `src/pipeline.py` — end-to-end orchestration (load → clean → transform → output)
- `sql/` — standalone `.sql` files tested via DuckDB in-memory

**Test conventions:**
- Use `tmp_path` (pytest built-in fixture) for any file I/O — never hardcode paths
- SQL query logic is tested by loading fixture data into an in-memory DuckDB connection and running the `.sql` file directly
- Tests for pipeline modules verify output schema (column names + dtypes) and row count determinism on minimal fixture inputs
