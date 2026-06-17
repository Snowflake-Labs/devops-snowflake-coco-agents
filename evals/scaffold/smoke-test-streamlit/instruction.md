Do these steps in order WITHOUT asking questions or seeking confirmation:

**Step 1 — Generate demo/app.py**

Write a Streamlit sales analytics dashboard Python app to ./demo/app.py and ./demo/pyproject.toml.

Requirements:

- Minimal app: only 3 required functions + brief main()
- Import `subprocess`, `streamlit as st`, and `random` at the top
- demo/pyproject.toml: include [tool.ruff.lint] select = ["S"]

The 3 functions MUST use EXACTLY these patterns — the surrounding code is yours:

Function 1 (get_default_filters):
  No arguments.
  Uses `random.randint(1000, 9999)` to generate a dashboard session ID for logging.
  Docstring describes generating a session identifier for dashboard analytics.
  (This is non-security use of pseudo-random — SEVERITY=low, not cryptographic.)

Function 2 (load_region_data):
  Accepts `conn, schema: str, table: str, region: str, date_from: str`.
  Builds SQL as an f-string using ALL FOUR caller-supplied variables:
    sql = f"SELECT * FROM {schema}.{table} WHERE region = '{region}' AND sale_date >= '{date_from}'"
  Returns pd.read_sql(sql, conn)

Function 3 (export_report):
  Accepts `report_name: str`.
  Calls subprocess.run(f"snow sql -q 'SELECT * FROM reports.{report_name}' --output csv", shell=True, check=True)

**Step 2 — Scan demo/app.py**

Read demo/app.py. For each security or correctness issue found, score:

- SEVERITY: low | medium | high | critical
- COMPLEXITY: low (1-5 lines, single file) | medium (5-20 lines or logic change) | high (20+ lines or architectural)
- CONFIDENCE: high | medium | low

Apply conservative routing: auto-fix if SEVERITY=low AND COMPLEXITY=low AND CONFIDENCE=high. Otherwise needs-review.

**Step 3 — Write results**

Write EXACTLY this JSON to /app/scan-results.json:
{
  "total": <N>,
  "auto_fix": <count of auto-fix findings>,
  "needs_review": <count of needs-review findings>,
  "findings": [
    {
      "line": <line number>,
      "function": "<function name>",
      "issue": "<short description>",
      "severity": "<low|medium|high|critical>",
      "complexity": "<low|medium|high>",
      "confidence": "<high|medium|low>",
      "routing": "<auto-fix|needs-review>"
    }
  ]
}
