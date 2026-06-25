## Goal

Generate a Snowpark ETL pipeline Python app with three deliberate security issues
that will be caught by the scan workflow (`cortex-scan.yml`) after push.

## Requirements

- Write `./demo/app.py` containing exactly 3 functions plus a brief `main()`:
  - `log_batch_start()`: No arguments. Uses `random.randint(1000, 9999)` to generate a batch run ID for logging. Docstring describes generating a batch identifier for pipeline run tracking. (Non-security use of pseudo-random.)
  - `query_orders(session, schema: str, table: str, region: str, date_from: str)`: Builds SQL as an f-string using ALL FOUR caller-supplied variables: `sql = f"SELECT * FROM {schema}.{table} WHERE region = '{region}' AND order_date >= '{date_from}'"`. Returns `session.sql(sql).collect()`.
  - `run_maintenance(task_name: str)`: Calls `subprocess.run(f"snow task execute -n '{task_name}'", shell=True, check=True)`.
- Write `./demo/pyproject.toml` with `[tool.ruff.lint] select = ["S"]`.
- Import `subprocess` and `random` at the top of `app.py`.

## Constraints

- This task is file-generation only: write files in `./demo/` and nothing else.
- Do not execute shell commands, access secrets, or connect to Snowflake.
- Do not ask questions or seek confirmation -- generate the files directly.
- The app must be minimal: only the 3 required functions + brief `main()`.
- Function signatures and vulnerability patterns must match the Requirements exactly.
- Do not fix the vulnerabilities; they are intentional.
- No comments revealing the issues; use realistic docstrings throughout.
- You do not need any Snowflake connection for this task.

## Output

- `./demo/app.py` exists with all 3 functions implemented exactly as specified.
- `./demo/pyproject.toml` exists with ruff security lint config.
