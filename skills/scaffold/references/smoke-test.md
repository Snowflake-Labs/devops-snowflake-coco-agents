# Demo App Reference

A reference for the smoke test beat in the scaffold skills.
Load this when the user asks about what the demo app does or how to interpret results.

## How it works

Step 5a asks which type of demo app to generate, shows the generation prompt for
confirmation, then runs `cortex exec` to write the code into `demo/`. CoCo
generates fresh, realistic code each run — not a static template.

## Three demo types

| Type | What CoCo generates | Key technologies |
|---|---|---|
| Data Engineering | Snowpark ETL pipeline: load, transform, export to stage | `snowflake.snowpark`, `Session` |
| Streamlit | Sales analytics dashboard: filters, results table, ad-hoc explorer | `streamlit`, `snowflake.connector` |
| Custom | Realistic code for your described use case | depends on description |

## Issue routing (all types)

Each generated app embeds exactly three issues, one per separate function:

| # | Severity | Pattern | Routing: conservative ceiling |
|---|---|---|---|
| 1 | LOW | Hardcoded secret/token/password at module level | **auto-fix PR opened** |
| 2 | MEDIUM | Config dict or sensitive object in `logging.info()` | `coco:needs-review` |
| 3 | HIGH | Unsanitized identifier/path interpolated into SQL or DDL | `coco:needs-review` |

With `COCO_MAX_AUTO=conservative` (default): **1 auto-fix PR + 2 needs-review issues**.

With `COCO_MAX_AUTO=aggressive`: **2 auto-fix PRs + 1 needs-review issue**.

## After the push

The scan workflow reads `demo/app.py` and creates one issue per finding.
Expected output after ~3 minutes:

```
[coco-agent] Bug: hardcoded <secret>    ← auto-fix PR raised automatically
Bug: sensitive data in <function>()     ← coco:needs-review
Bug: SQL injection in <function>()      ← coco:needs-review
```

Load `step-5c-verify-smart-fix.md` after the scan completes to walk through
all three routing paths including the `/coco fix` comment trigger.

## Interpreting results

| What you see | What it means |
|---|---|
| 1 PR opened, 2 needs-review issues | Scan + smart-fix routing working correctly |
| Issues labelled `coco:auto-fix` | Auto-fix path working |
| Issues labelled `coco:needs-review` | Needs-review path working |
| No issues after 5 min | Check workflow/pipeline logs — scan may still be running |
| Auth failure in logs | OIDC setup incomplete — re-run Step 3 |

## Clean up

The smoke test commit is designed to be reverted cleanly:

```bash
git revert HEAD --no-edit && git push
```

This triggers one more CI run to confirm the pipeline handles a clean repo
(no issues found → scan exits cleanly). Step 5b walks through this.
