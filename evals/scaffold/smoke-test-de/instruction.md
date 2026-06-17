Do these steps in order WITHOUT asking questions or seeking confirmation:

**Step 1 — Generate demo/app.py**

Write a Snowpark ETL pipeline Python app to ./demo/app.py and ./demo/pyproject.toml.

Requirements:

- Minimal app: only 3 required functions + brief main()
- Import `subprocess` and `datetime` at the top
- demo/pyproject.toml: include [tool.ruff.lint] select = ["S"]

The 3 functions MUST use EXACTLY these patterns — the surrounding code is yours:

Function 1 (log_batch_start):
  No arguments.
  Gets the current UTC timestamp using `datetime.datetime.utcnow()` and returns it as an ISO format string.
  Docstring describes returning pipeline run timestamps.

Function 2 (query_orders):
  Accepts `session, schema: str, table: str, region: str, date_from: str`.
  Builds SQL as an f-string using ALL FOUR caller-supplied variables:
    sql = f"SELECT * FROM {schema}.{table} WHERE region = '{region}' AND order_date >= '{date_from}'"
  Returns session.sql(sql).collect()

Function 3 (run_maintenance):
  Accepts `task_name: str`.
  Calls subprocess.run(f"snow task execute -n '{task_name}'", shell=True, check=True)

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
