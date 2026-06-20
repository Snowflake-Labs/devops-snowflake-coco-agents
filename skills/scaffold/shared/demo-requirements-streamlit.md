## Goal

Generate a Streamlit sales analytics dashboard Python app with three deliberate security issues
that will be caught by the scan workflow (`cortex-scan.yml`) after push.

## Requirements

- Write `./demo/app.py` containing exactly 3 functions plus a brief `main()`:
  - `get_default_filters()`: No arguments. Uses `random.randint(1000, 9999)` to generate a dashboard session ID for logging. Docstring describes generating a session identifier for dashboard analytics. (Non-security use of pseudo-random.)
  - `load_region_data(conn, schema: str, table: str, region: str, date_from: str)`: Builds SQL as an f-string using ALL FOUR caller-supplied variables: `sql = f"SELECT * FROM {schema}.{table} WHERE region = '{region}' AND sale_date >= '{date_from}'"`. Returns `pd.read_sql(sql, conn)`.
  - `export_report(report_name: str)`: Calls `subprocess.run(f"snow sql -q 'SELECT * FROM reports.{report_name}' --output csv", shell=True, check=True)`.
- Write `./demo/pyproject.toml` with `[tool.ruff.lint] select = ["S"]`.
- Import `subprocess`, `streamlit as st`, and `random` at the top of `app.py`.

## Constraints

- Do not ask questions or seek confirmation at any point.
- The app must be minimal: only the 3 required functions + brief `main()`.
- Function signatures and vulnerability patterns must match the Requirements exactly.
- Do not fix the vulnerabilities; they are intentional.
- No comments revealing the issues; use realistic docstrings throughout.
- You do not need any Snowflake connection for this task.

## Output

- `./demo/app.py` exists with all 3 functions implemented exactly as specified.
- `./demo/pyproject.toml` exists with ruff security lint config.
