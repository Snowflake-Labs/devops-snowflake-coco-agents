# GitHub Demo Walkthrough

A step-by-step test run of the GitHub scaffold skill. Follow in order — expected
outputs are shown so you can verify before moving on.

## Pre-flight checklist

- [ ] `gh auth status` — correct account is active
- [ ] `snow connection test` — succeeds
- [ ] CoCo plugin installed: `cortex plugin list | grep devops-coco-agents`
- [ ] Snowflake account identifier ready (e.g. `xy12345.us-east-1`)

## Start the scaffold

Type in the CoCo chat panel:

```
scaffold for github
```

The skill asks: **Quick start or Full setup?** — choose Quick start for a 10-minute run,
Full setup to also run the smoke test and watch issues + PRs appear.

---

## Step 1 — Create Project

**Skill asks:**

- Setup mode → Quick start / Full setup
- GitHub account → confirm or switch
- Project type → New repo (from template) / Add to existing
- Repo name → skill generates a petname like `ksampath/nimble-proxy` (edit freely)
- Visibility → Private (default)
- Snowflake prefix → e.g. `DEMO`
- Snowflake account → your account identifier

**Expected plan output:**

```
Creates: ksampath/nimble-proxy  (private, from template)
Clones:  ./nimble-proxy         (clean single commit — no template history)
```

**Verify:**
- New private repo visible at `https://github.com/ksampath/nimble-proxy`
- Local directory `nimble-proxy/` created

---

## Step 2 — Hold Before Go-Live

CoCo confirms GitHub Actions are disabled before Snowflake credentials are set.

**Expected output:** `false` — Actions are off.

This prevents half-configured pipelines from running and failing with OIDC errors.

---

## Step 3 — Connect Snowflake

CoCo provisions three Snowflake objects:

| Object | Example value |
|--------|--------------|
| Role | `DEMO_GH_NIMBLE_PROXY_COCO_AGENT_ROLE` |
| Warehouse | `DEMO_GH_NIMBLE_PROXY_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `DEMO_GH_NIMBLE_PROXY_COCO_AGENT_USER` (TYPE = SERVICE) |

OIDC trust is bound to `repo:ksampath/nimble-proxy:ref:refs/heads/main`.
No password is stored. GitHub issues a short-lived token that Snowflake verifies directly.

**Verify:**
```sql
SHOW USERS LIKE 'DEMO_GH_%_COCO_AGENT_USER';
```

---

## Step 4 — Configure

CoCo sets CI secrets and the fix-mode ceiling:

| Secret / Variable | Value |
|-------------------|-------|
| `SNOWFLAKE_ACCOUNT` | your account |
| `SNOWFLAKE_ROLE` | `DEMO_GH_NIMBLE_PROXY_COCO_AGENT_ROLE` |
| `SNOWFLAKE_WAREHOUSE` | `DEMO_GH_NIMBLE_PROXY_COCO_AGENT_WH` |
| `COCO_MAX_AUTO` (variable) | `conservative` |

**Quick start path:** after secrets are set, CoCo re-enables Actions and applies
branch protection (require 1 PR review). Done.

**Full setup path:** also asks whether to install a local runner, then offers the smoke test.

---

## Step 5 — Watch the Loop (full setup only)

CoCo copies a small Python app with three intentional bugs into `demo/`, enables Actions,
and pushes. The scan workflow finds the bugs, raises issues, and the fix workflow opens PRs.

**After a minute, expected output:**

```
=== Issues ===
[coco-agent] Bug: SQL injection risk in query_table()
[coco-agent] Bug: hardcoded credentials in get_connection()
[coco-agent] Bug: undefined reference in process_data()

=== PRs ===
fix(coco-agent): SQL injection risk in query_table()       (open)
fix(coco-agent): hardcoded credentials in get_connection() (open)
fix(coco-agent): undefined reference in process_data()     (open)
```

Three issues, three PRs — fully automated. Each PR is one minimal fix so they
don't conflict with each other.

---

## Step 6 — Clean Up (optional)

The skill offers three options:

- **Yes, tear down everything** — deregisters runner, drops Snowflake objects, deletes repo
- **Drop Snowflake only** — keeps the repo
- **Keep everything**

**Verify after full teardown:**
```bash
gh api "repos/ksampath/nimble-proxy" 2>&1  # should return 404
snow sql -q "SHOW USERS LIKE 'DEMO_GH_%_COCO_AGENT_USER';"  # should return 0 rows
```
