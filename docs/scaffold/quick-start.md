# Quick Start

Quick start mode provisions the essentials in ~10 minutes — no local runner, no smoke test.
Works for both new repos (greenfield) and existing repos (brownfield).

## What you get

- Repo/project from template with clean git history
- Snowflake OIDC SERVICE user provisioned
- CI secrets and fix-mode ceiling set
- Actions/pipelines re-enabled
- Branch protection applied

## What's skipped

- Smoke test (step 5)

## How to choose

When the scaffold skill starts, it asks:

```text
How would you like to set up CoCo?

  Quick start — cloud runners
    Create project → Snowflake OIDC → set secrets → done in ~10 min.

  Full setup — with smoke test
    All steps including an end-to-end validation run.
```

Choose **Quick start**.

## After quick start

CI is live immediately — push any code to `main` to trigger the scan workflow.

To run the smoke test later, start a Full setup or re-run Step 5 — CoCo will ask which demo type to generate (DE / Streamlit / Custom), preview the prompt, and write the app directly into `demo/`.

To change the fix ceiling, edit `.github/coco-config.yml` (or `.gitlab/coco-config.yml`) via PR:

```yaml
fix_mode:
  max_auto: aggressive  # was: conservative
```

## Brownfield (existing repo)

Quick start works identically for existing repos. The skill:

1. Clones the existing repo
2. Adds CoCo CI workflow files (`.github/workflows/cortex-scan.yml` + `cortex-fix.yml`)
3. Temporarily disables Actions during Snowflake setup
4. Provisions OIDC and sets secrets
5. Re-enables Actions and applies branch protection

!!! note
    For existing repos that already have branch protection rules, the skill detects and
    preserves them — it will not overwrite your existing policy.
