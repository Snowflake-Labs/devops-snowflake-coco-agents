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

Read the full requirements from the appropriate shared file based on `<TYPE>`:
- DE: Read `skills/scaffold/shared/demo-requirements-de.md` using your Read tool
- Streamlit: Read `skills/scaffold/shared/demo-requirements-streamlit.md` using your Read tool

The file contains a complete IDD-structured prompt (Goal, Requirements, Constraints, Output).
Execute ALL instructions in that file exactly as written — generate the demo app, scan it, and create the issue files.

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
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_4
```

Write the files directly into `$REPO_OR_PROJECT_NAME/demo/` using your **Write tool**.

```bash
cd "$REPO_OR_PROJECT_NAME"
git add demo/
git commit -m "test(smoke): generate $APP_TYPE demo app for CI/CD loop validation"
git push
```

Return to calling platform step to verify CI triggered and watch the loop.
