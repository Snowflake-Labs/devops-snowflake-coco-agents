# Scaffold — GitHub

The GitHub scaffold skill sets up an Agentic DevOps pipeline with Snowflake CoCo
on GitHub Actions in one guided conversation.

## What gets created

- A GitHub repo from the [github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) template
- Three Snowflake objects (role, warehouse, SERVICE user) with OIDC trust
- Five GitHub secrets + `COCO_MAX_AUTO` repository variable
- Branch protection (require 1 PR review)
- `.github/coco-config.yml` with `conservative` fix ceiling

## The 6 steps

### Step 1 — Create Project

Asks: setup mode, project type (new / import), repo name, visibility, Snowflake prefix and account.

For a new repo: creates from template, disables Actions immediately.
For an existing repo: clones and adds CI workflow files with `[skip ci]` to prevent premature runs.

### Step 2 — Hold Before Go-Live

Confirms GitHub Actions are disabled. For existing repos, disables them now.

### Step 3 — Connect Snowflake

Provisions the OIDC SERVICE user:

```sql
CREATE USER IF NOT EXISTS $SF_USER TYPE = SERVICE;
ALTER USER $SF_USER SET WORKLOAD_IDENTITY = (
  TYPE    = OIDC
  ISSUER  = 'https://token.actions.githubusercontent.com'
  SUBJECT = 'repo:$REPO_PATH:ref:refs/heads/main'
);
```

### Step 4 — Configure

**Quick start:** sets secrets + `COCO_MAX_AUTO`, re-enables Actions, applies branch protection. Done.

**Full setup:** also asks whether to install a local runner. If yes, installs to `.github/runner/` and asks whether to run the smoke test.

### Step 5 — Watch the Loop (full setup)

Pushes a sample app with 3 intentional bugs. Scan workflow fires, issues are raised,
fix PRs are opened. See [Demo walkthrough →](../demo/github.md)

### Step 6 — Clean Up

Tears down everything in dependency order: disable Actions → deregister runner →
drop Snowflake objects → delete repo → remove local clone.

## Authentication

The CI pipeline uses Workload Identity Federation — no `SNOWFLAKE_PAT` is needed on
GitHub-hosted runners. The `snowflake-cli-action@v2` handles OIDC token exchange automatically.
