## Goal

Generate a Streamlit sales analytics dashboard Python app with three deliberate security issues, then scan it using the production routing policy to produce correctly-formatted GitHub issue files that match what `cortex-scan.yml` would create in CI.

## Requirements

### Phase 1: Generate demo app

- Write `./demo/app.py` containing exactly 3 functions plus a brief `main()`:
  - `get_default_filters()`: No arguments. Uses `random.randint(1000, 9999)` to generate a dashboard session ID for logging. Docstring describes generating a session identifier for dashboard analytics. (Non-security use of pseudo-random.)
  - `load_region_data(conn, schema: str, table: str, region: str, date_from: str)`: Builds SQL as an f-string using ALL FOUR caller-supplied variables: `sql = f"SELECT * FROM {schema}.{table} WHERE region = '{region}' AND sale_date >= '{date_from}'"`. Returns `pd.read_sql(sql, conn)`.
  - `export_report(report_name: str)`: Calls `subprocess.run(f"snow sql -q 'SELECT * FROM reports.{report_name}' --output csv", shell=True, check=True)`.
- Write `./demo/pyproject.toml` with `[tool.ruff.lint] select = ["S"]`.
- Import `subprocess`, `streamlit as st`, and `random` at the top of `app.py`.

### Phase 2: Scan and create issues

- Read `demo/app.py` and identify security vulnerabilities.
- Score each finding on three risk dimensions:
  - SEVERITY: critical | high | medium | low
  - COMPLEXITY: low (single file, 1-5 lines changed) | medium (1-2 files, 5-20 lines) | high (3+ files, 20+ lines, architectural)
  - CONFIDENCE: high | medium | low (certainty about the correct fix)
- Apply conservative ceiling routing (`COCO_MAX_AUTO=conservative`):
  - auto-fix only when SEVERITY=low AND COMPLEXITY=low AND CONFIDENCE=high
  - all other combinations -> needs-review
- Write `/app/scan-results.json`:
  ```json
  {
    "total": <N>,
    "auto_fix": <count>,
    "needs_review": <count>,
    "findings": [
      {
        "line": <line number>,
        "function": "<function name>",
        "issue": "<short description>",
        "severity": "<critical|high|medium|low>",
        "complexity": "<low|medium|high>",
        "confidence": "<high|medium|low>",
        "routing": "<auto-fix|needs-review>"
      }
    ]
  }
  ```
- For each finding, write a GitHub issue JSON file to `/app/issues/` matching the production scan format:
  - Filename: `issue-<N>.json` (numbered sequentially starting at 1, security issues first)
  - For auto-fix findings:
    ```json
    {
      "title": "[coco-agent] Bug: <short description>",
      "body": "demo/app.py:<function>\n\nCode: <problematic code snippet>\nProblem: <why it is a bug>\nExpected: <what the correct behaviour should be>\n\n---\n_Severity: <SEVERITY> | Complexity: <COMPLEXITY> | Confidence: <CONFIDENCE> | Fix mode: auto_",
      "labels": ["coco-agent", "coco:auto-fix", "coco-agent-security"]
    }
    ```
  - For needs-review findings:
    ```json
    {
      "title": "Bug: <short description>",
      "body": "demo/app.py:<function>\n\nCode: <problematic code snippet>\nProblem: <why it is a bug>\nExpected: <what the correct behaviour should be>\n\n---\n_Severity: <SEVERITY> | Complexity: <COMPLEXITY> | Confidence: <CONFIDENCE> | Fix mode: needs-review_\n_To trigger fix: comment `/coco fix` on this issue._",
      "labels": ["coco:needs-review", "coco-agent-security"]
    }
    ```
- Print a final summary line to stdout: `Scan complete. Found N issue(s) [auto-fix: X, needs-review: Y]. Ceiling: conservative`

## Constraints

- Do not ask questions or seek confirmation at any point.
- The app must be minimal: only the 3 required functions + brief `main()`.
- Function signatures and vulnerability patterns must match Phase 1 exactly.
- Do not fix the vulnerabilities; they are intentional.
- Each finding must have exactly one corresponding issue file.
- Emit security issues in priority order (critical first, then high, then low).
- You do not need any Snowflake connection for this task.

## Output

- `./demo/app.py` exists with all 3 functions implemented exactly as specified.
- `./demo/pyproject.toml` exists with ruff security lint config.
- `/app/scan-results.json` exists with valid JSON matching the schema above.
- `/app/issues/` directory contains one JSON file per finding.
- The `random.randint()` finding (SEVERITY=low) has title prefix `[coco-agent] Bug:` and labels including `coco:auto-fix`.
- The SQL f-string injection (SEVERITY=high) has title `Bug:` and labels including `coco:needs-review`.
- The subprocess shell injection (SEVERITY=critical) has title `Bug:` and labels including `coco:needs-review`.
