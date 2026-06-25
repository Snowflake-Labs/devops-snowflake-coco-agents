# GitHub Demo Walkthrough

A step-by-step test run of the GitHub scaffold skill. Follow in order — expected
outputs are shown so you can verify before moving on.

## Pre-flight checklist

- [ ] `gh auth status` — correct account is active
- [ ] `snow connection test --connection local-oauth` — succeeds
- [ ] CoCo plugin installed: `cortex plugin list | grep devops-coco-agents`
- [ ] Snowflake account identifier ready (e.g. `xy12345.us-east-1`)

## Start the scaffold

Type in the CoCo chat panel:

```text
$devops-coco-agents:scaffold-for-github
```

The skill asks: **Quick start or Full setup?** Choose Quick start for a 10-minute run,
Full setup to also run the smoke test and walk through the smart-fix verification.

---

## Step 1 — Create Project

**Skill asks:**

- Setup mode → Quick start / Full setup
- GitHub account → confirm or switch
- Project type → New repo (from template) / Add to existing
- Repo name → skill generates a petname like `youruser/nimble-proxy` (edit freely)
- Visibility → Private (default)
- Snowflake prefix → e.g. `DEMO`
- Snowflake account → your account identifier

**Expected plan output:**

```text
Creates: youruser/nimble-proxy  (private, from template)
Clones:  ./nimble-proxy         (clean single commit — no template history)
```

**Verify:**

```bash
gh repo view youruser/nimble-proxy --json name,private,url
```

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

OIDC trust is bound to `repo:youruser/nimble-proxy:ref:refs/heads/main`.
No password is stored — GitHub issues a short-lived token that Snowflake verifies directly.

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

**Full setup path:** also offers the smoke test below.

---

## Step 5 — Watch the Loop (full setup only)

CoCo asks which demo app type to generate (DE / Streamlit / Custom), shows a
generation prompt for confirmation, then writes the files directly into `demo/`
using its Write tool. Actions are enabled and the commit is pushed.

### What the scan finds

| Issue | Severity | Routing (conservative) |
|-------|----------|----------------------|
| `FALLBACK_DB_CONN = "dev-placeholder-replace-before-deploy"` | low | **auto-fix** |
| `f"SELECT * FROM {table_name} WHERE amount > 0"` | high | **needs-review** |
| `subprocess.run(f"snow sql -q '{cmd}'", shell=True)` | critical | **needs-review** |

### Beat 1 — Ceiling source

Check the scan job summary for the active ceiling:

```bash
gh run list --repo youruser/nimble-proxy --workflow cortex-scan.yml --limit 1
```

Look for this line in the job summary:

```
::notice::Fix ceiling: conservative (source: .github/coco-config.yml)
```

### Beat 2 — Auto-fix PR (low severity)

```bash
gh issue list --repo youruser/nimble-proxy --label "coco:auto-fix"
gh pr list   --repo youruser/nimble-proxy --state open
```

Expected: 1 issue labeled `coco:auto-fix`, 1 PR fixing the `FALLBACK_DB_CONN` placeholder.

### Beat 3 — Needs-review labels (medium + high severity)

```bash
gh issue list --repo youruser/nimble-proxy --label "coco:needs-review"
```

Expected: 2 issues — f-string SQL injection (high/medium) + subprocess shell=True injection (critical/high).

### Beat 4 — Comment trigger (`/coco fix`)

Trigger the fix on the SQL injection (f-string) needs-review issue:

```bash
ISSUE_NUM=$(gh issue list --repo youruser/nimble-proxy --label "coco:needs-review" \
  --json number,title \
  --jq '[.[] | select(.title | test("sql|select|inject"; "i"))] | .[0].number')
gh issue comment "$ISSUE_NUM" --repo youruser/nimble-proxy --body "/coco fix"
```

Watch `cortex-comment-fix.yml` trigger:

```bash
gh run list --repo youruser/nimble-proxy --workflow cortex-comment-fix.yml --limit 3
```

Expected: fix workflow fires, PR raised for the logging issue within ~2 minutes.

---

## Step 6 — Clean Up (optional)

The skill offers three options:

- **Yes, tear down everything** — drops Snowflake objects, deletes repo
- **Drop Snowflake only** — keeps the repo
- **Keep everything**

**Verify after full teardown:**

```bash
gh api "repos/youruser/nimble-proxy" 2>&1          # should return 404
snow sql -q "SHOW USERS LIKE 'DEMO_GH_%_COCO_AGENT_USER';"  # 0 rows
```
