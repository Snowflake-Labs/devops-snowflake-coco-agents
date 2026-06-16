# Step 5a: Smoke Test — Choose & Preview (GitHub)

> Sub-step of Step 5. Enables Actions, asks demo type, builds and previews the generation prompt.

**Enable Actions:**

```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": true}'
```

**Verify:** `gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled` → `true`.

---

## Ask

```
ask_user_question:
  header: "Demo type"
  question: "Which app should CoCo generate? (1 auto-fix PR + 2 needs-review)"
  options:
    - label: "Data Engineering — Snowpark ETL pipeline"
    - label: "Streamlit — sales analytics dashboard"
    - label: "Custom — describe your own use case"
    - label: "Skip smoke test"
```

If **Skip**: load `github/steps/step-5b-revert.md`.

If **Custom**: ask (text, `defaultValue: "data analytics pipeline"`) for the use case. Store as `$USE_CASE_DESC`.

DE description: *"A Snowpark order-processing pipeline: loads raw records from stage, validates and transforms, then exports a clean report to an internal stage."*

Streamlit description: *"A Streamlit sales analytics dashboard: connects to Snowflake, filters by region, renders results, and supports a custom table explorer."*

---

## Build + preview prompt

Construct this prompt with `<TYPE>` and `<USE_CASE>` substituted:

```
[Goal]
Write a realistic <TYPE> Python demo app into ./demo/.

[Use case]
<USE_CASE>

[Requirements]
- Write demo/app.py — minimal: only the 3 required functions + a brief main(), nothing extra
- Write demo/pyproject.toml ([tool.ruff] selecting = ["S"])
- 3 issues in 3 separate functions (no issue-combining):
    Issue 1 (LOW):    hardcoded secret/token/password at module level
    Issue 2 (MEDIUM): call `logger.info("Running with config: %s", run_config)` where
                      run_config is a dict — use module-level logger, not root logging
    Issue 3 (HIGH):   unsanitized identifier or path interpolated into SQL/DDL
- No comments revealing the issues; realistic docstrings throughout

[Output]
Use your Write tool to create the files. No explanation needed.
```

⚠️ MANDATORY: `enter_plan_mode` → display the full prompt above → `exit_plan_mode`.

```
ask_user_question:
  header: "Confirm"
  question: "Run this prompt to generate the demo app?"
  options:
    - label: "Yes — generate and push"
    - label: "Change use case"
    - label: "Cancel"
```

If **Change use case**: loop back to Custom text input above.
If **Cancel**: load `github/steps/step-5b-revert.md`.

When confirmed, load `github/steps/step-5a-generate.md`.
