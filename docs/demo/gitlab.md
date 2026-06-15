# GitLab Demo Walkthrough

A step-by-step test run of the GitLab scaffold skill. Follow in order — expected
outputs are shown so you can verify before moving on.

## Pre-flight checklist

- [ ] `glab auth status` — correct account is active
- [ ] `snow connection test` — succeeds
- [ ] CoCo plugin installed: `cortex plugin list | grep devops-coco-agents`
- [ ] Snowflake account identifier ready (e.g. `xy12345.us-east-1`)

## Start the scaffold

```
scaffold for gitlab
```

---

## Step 1 — Create Project

**Skill asks:**

- Setup mode → Quick start / Full setup
- glab auth confirmed (hard gate — skill stops if not authenticated)
- Project type → New project (from template) / Add to existing
- Project path → skill generates a petname like `ksampath/nimble-proxy` (edit freely)
- Visibility → Private (default)
- Snowflake prefix → e.g. `DEMO`
- Snowflake account → your account identifier

**Expected plan output:**

```
Creates: ksampath/nimble-proxy  (private, from template)
Clones:  ./nimble-proxy         (clean single commit — no template history)
```

---

## Step 2 — Hold Before Go-Live

CoCo confirms CI/CD pipelines are disabled before configuring Snowflake credentials.

**Expected output:** `"disabled"` — pipelines are off.

---

## Step 3 — Connect Snowflake

CoCo provisions three Snowflake objects:

| Object | Example value |
|--------|--------------|
| Role | `DEMO_GL_NIMBLE_PROXY_COCO_AGENT_ROLE` |
| Warehouse | `DEMO_GL_NIMBLE_PROXY_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `DEMO_GL_NIMBLE_PROXY_COCO_AGENT_USER` (TYPE = SERVICE) |

OIDC trust is bound to `project_path:ksampath/nimble-proxy:ref_type:branch:ref:main`.

---

## Step 4 — Configure

The skill collects the bot token (needed to create MRs and issues):

```
Use your glab auth token (convenient)
  OR
Use a dedicated long-lived PAT (api + write_repository scopes)
```

Then sets 6 CI/CD variables:

| Variable | Masked |
|----------|--------|
| `SNOWFLAKE_ACCOUNT` | yes |
| `SNOWFLAKE_USER` | no |
| `SNOWFLAKE_WAREHOUSE` | no |
| `SNOWFLAKE_ROLE` | no |
| `GITLAB_TOKEN_coco` | yes |
| `COCO_MAX_AUTO` | no (value: `conservative`) |

**Quick start:** after variables are set, CoCo re-enables pipelines and applies
branch protection (push restricted to MRs). Done.

---

## Step 5 — Watch the Loop (full setup only)

Same smoke test as GitHub — three intentional bugs, scan finds them, fix agent
opens MRs automatically.

```
=== Issues ===
[coco-agent] Bug: SQL injection risk in query_table()
...

=== MRs ===
fix(coco-agent): SQL injection risk in query_table()  (open)
...
```

---

## Step 6 — Clean Up (optional)

- **Yes, tear down everything** — deregisters runner, drops Snowflake objects, deletes project
- **Drop Snowflake only** — keeps project
- **Keep everything**

**Verify:**
```bash
glab api "projects/ksampath%2Fnimble-proxy" 2>&1  # should 404
snow sql -q "SHOW USERS LIKE 'DEMO_GL_%_COCO_AGENT_USER';"  # 0 rows
```
