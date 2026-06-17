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
- 3 issues in 3 separate functions (no issue-combining):
    Issue 1 (LOW):    hardcoded secret/token/password at module level
    Issue 2 (MEDIUM): call `logger.info("Running with config: %s", run_config)`
                      (run_config is a dict; use module-level logger)
    Issue 3 (HIGH):   unsanitized identifier or path interpolated into SQL/DDL
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
