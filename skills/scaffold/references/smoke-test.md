# Demo Test Reference

A shared reference for the optional smoke test beat in the scaffold skills.
Load this when the user asks to test the workflow with a sample app.

## What the templates contain

The templates at `skills/scaffold/templates/` contain a minimal Python app with
**3 intentional issues**, one per smart-fix severity tier:

| # | File | Issue | Severity | Complexity | Confidence | Conservative | Aggressive |
|---|------|-------|----------|------------|------------|-------------|------------|
| 1 | `app.py` | Hardcoded schema: `SCHEMA = "PUBLIC"` | low | low | high | **auto-fix** | auto-fix |
| 2 | `app.py` | Sensitive data in debug log: `_LOG.debug("account=%s user=%s", ...)` | medium | low | high | needs-review | **auto-fix** |
| 3 | `app.py` | SQL injection: `f"SELECT * FROM {table_name}"` | high | medium | medium | needs-review | needs-review |

With the default `conservative` ceiling you will see **1 auto-fix PR + 2 needs-review issues**.
Switching `COCO_MAX_AUTO` to `aggressive` changes that to **2 auto-fix + 1 needs-review**.

`pyproject.toml` enables ruff's `S` (bandit security) rules, which catch issues 2 and 3 reliably.

## How to copy the templates

Read each file from `skills/scaffold/templates/smoke-test/` and write it to `demo/` in the user's repo:

```
skills/scaffold/templates/smoke-test/app.py            → <repo>/demo/app.py
skills/scaffold/templates/smoke-test/pyproject.toml    → <repo>/demo/pyproject.toml
skills/scaffold/templates/smoke-test/tests/__init__.py → <repo>/demo/tests/__init__.py
skills/scaffold/templates/smoke-test/tests/test_app.py → <repo>/demo/tests/test_app.py
```

Commit as a revertable test commit:

```bash
cd <repo>
git add demo/
git commit -m "test(smoke): add intentional-issue app for CI/CD loop validation"
git push
```

Once the loop has validated, clean up with a single revert:

```bash
git revert HEAD --no-edit && git push
```

## What happens when you push

The scan workflow reads `demo/app.py` and creates one issue per finding:

```
[coco-agent] Bug: hardcoded schema in app.py           ← auto-fix PR raised
Bug: sensitive data in debug log in get_connection()   ← coco:needs-review
Bug: SQL injection risk in query_table()               ← coco:needs-review
```

After the scan, load `step-5c-verify-smart-fix.md` to walk through all three
routing paths including the `/coco fix` comment trigger.

## Interpreting results

| What you see | What it means |
|---|---|
| 1 PR opened, 2 needs-review issues | Scan + smart-fix routing working correctly (conservative) |
| Issues with `coco:auto-fix` label | Auto-fix path working |
| Issues with `coco:needs-review` label | Needs-review path working |
| No issues after 5 min | Scan may still be running — check workflow/pipeline logs |
| Auth failure in logs | OIDC setup incomplete — re-run step 3 |
