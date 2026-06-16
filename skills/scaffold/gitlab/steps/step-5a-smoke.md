# Step 5a: Smoke Test — Choose & Preview (GitLab)

> Sub-step of Step 5. Enables pipelines, asks demo type, builds and previews the generation prompt.

```bash
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

**Enable pipelines:**

```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```

**Verify:** `glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"` → `enabled`.

---

## Ask

```
ask_user_question:
  header: "Demo type"
  question: "Which app should CoCo generate? (1 auto-fix MR + 2 needs-review)"
  options:
    - label: "Data Engineering — Snowpark ETL pipeline"
    - label: "Streamlit — sales analytics dashboard"
    - label: "Custom — describe your own use case"
    - label: "Skip smoke test"
```

If **Skip**: load `gitlab/steps/step-5b-revert.md`.

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
- Write demo/app.py and demo/pyproject.toml ([tool.ruff] selecting = ["S"])
- 3 issues in 3 separate functions (no issue-combining):
    Issue 1 (LOW):    hardcoded secret/token/password at module level
    Issue 2 (MEDIUM): config dict or sensitive object in logging.info()
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
If **Cancel**: load `gitlab/steps/step-5b-revert.md`.

When confirmed, load `gitlab/steps/step-5a-generate.md`.
