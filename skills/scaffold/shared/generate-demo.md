# Shared: Generate Demo App

> Loaded from platform step-5a after CI is enabled.
> `$REPO_OR_PROJECT_NAME` (local clone dir) set by calling step.

---

## Ask

```
ask_user_question:
  header: "Demo type"
  question: "Which app should CoCo generate? (1 auto-fix + 2 needs-review)"
  options:
    - label: "Data Engineering — Snowpark ETL pipeline"
    - label: "Streamlit — sales analytics dashboard"
    - label: "Custom — describe your own use case"
    - label: "Skip smoke test"
```

If **Skip**: load the calling platform's `step-5b-revert.md`.
If **Custom**: ask (text, `defaultValue: "data analytics pipeline"`). Store as `$USE_CASE_DESC`.
DE: *"Snowpark order-processing pipeline: loads from stage, transforms, exports to internal stage."*
Streamlit: *"Streamlit sales dashboard: Snowflake connection, region filters, results table, ad-hoc query explorer."*

---

## Build + preview prompt

Construct with `<TYPE>` and `<USE_CASE>` substituted:

```
[Goal]
Write a realistic <TYPE> Python demo app into ./demo/.

[Use case]
<USE_CASE>

[Requirements]
- Write demo/app.py — minimal: only 3 required functions + brief main()
- Write demo/pyproject.toml ([tool.ruff] selecting = ["S"])
- 3 issues in 3 separate functions (no issue-combining). Each routes to a
  DIFFERENT fix mode under COCO_MAX_AUTO=conservative:
    Issue 1 (auto-fix):   a function that calls `datetime.datetime.utcnow()`
      to get a timestamp. This is deprecated since Python 3.12 — use
      `datetime.datetime.now(datetime.timezone.utc)` instead.
      - SEVERITY=low (code quality / deprecation, not a security issue)
      - Complexity=low (1-line fix), Confidence=high → auto-fix ✓
      - Import `datetime` at the top of the file (no other datetime imports)
    Issue 2 (needs-review, /coco fix target): f-string SQL injection via a
      function parameter: `f"SELECT * FROM {table_name} WHERE amount > 0"`
      Severity=high, Complexity=medium (requires parameterized query).
    Issue 3 (needs-review, stays open): subprocess command injection:
      `subprocess.run(f"snow sql -q '{cmd}'", shell=True, check=True)`
      Import subprocess at top of file.
      Severity=critical, Complexity=high (shell=True is architectural).
- No comments revealing the issues; realistic docstrings throughout
[Output]
Use your Write tool to create the files. No explanation needed.
```

⚠️ MANDATORY: `enter_plan_mode` → display full prompt → `exit_plan_mode`.

```
ask_user_question:
  header: "Confirm"
  question: "Run this prompt to generate the demo app?"
  options:
    - label: "Yes — generate and push"
    - label: "Change use case"
    - label: "Cancel"
```

If **Change use case**: loop back to Custom text input. If **Cancel**: load calling platform's `step-5b-revert.md`.

---

## Generate + commit

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_5
```

Write the files directly into `$REPO_OR_PROJECT_NAME/demo/` using your **Write tool**.

```bash
cd "$REPO_OR_PROJECT_NAME"
git add demo/
git commit -m "test(smoke): generate $APP_TYPE demo app for CI/CD loop validation"
git push
```

Return to calling platform step to verify CI triggered and watch the loop.
