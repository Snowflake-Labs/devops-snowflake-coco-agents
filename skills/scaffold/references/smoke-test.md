# Demo Test Reference

A shared reference for the optional demo test beat in the scaffold skills.
Load this when the user asks to test the workflow with a sample app.

## What the Demo Templates Contain

The templates at `skills/scaffold/templates/` contain a minimal Python app with
**3 intentional issues** that Cortex is designed to find and fix:

| File | Issue | Description |
|------|-------|-------------|
| `app.py` | Hardcoded schema | `SCHEMA = "PUBLIC"` — should come from an env var |
| `app.py` | Password auth | `password=os.environ.get("SNOWFLAKE_PASSWORD", "")` — should use `WORKLOAD_IDENTITY` or `externalbrowser` |
| `app.py` | SQL injection | `f"SELECT * FROM {table_name}"` — should use a quoted identifier or allowlist |

`pyproject.toml` enables ruff's `S` (bandit security) rules, which reliably catch issues 2 and 3.

## How to Copy the Templates

Read each file from `skills/scaffold/templates/smoke-test/` and write it to `demo/` in the user's repo:

```
skills/scaffold/templates/smoke-test/app.py           → <repo>/demo/app.py
skills/scaffold/templates/smoke-test/pyproject.toml   → <repo>/demo/pyproject.toml
skills/scaffold/templates/smoke-test/tests/__init__.py → <repo>/demo/tests/__init__.py
skills/scaffold/templates/smoke-test/tests/test_app.py → <repo>/demo/tests/test_app.py
```

Then commit as a **revertable test commit**:
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

## What Happens When You Push

The scan workflow/job reads `demo/app.py` and asks Cortex to review it.
For each issue found, it creates a `[coco-agent]` issue:

```
[coco-agent] Bug: hardcoded schema in app.py
[coco-agent] Bug: password authentication in get_connection()
[coco-agent] Bug: SQL injection risk in query_table()
```

Each `[coco-agent]` issue triggers the fix workflow/job automatically.
Cortex reads the issue, locates the code, applies the minimal fix, commits
to a branch, and opens a PR/MR. The cycle completes end-to-end without
any human intervention.

## Interpreting Results

| What you see | What it means |
|---|---|
| Issues created with `[coco-agent]` label | Scan ran successfully |
| PRs/MRs opened against new branches | Fix jobs ran and applied changes |
| No issues after 5 min | Scan may still be running — check the workflow/pipeline logs |
| Auth failure in logs | OIDC setup incomplete — re-run Beat 3 |
