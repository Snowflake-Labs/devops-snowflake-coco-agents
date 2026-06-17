# GitLab Demo Walkthrough

A step-by-step test run of the GitLab scaffold skill. Follow in order — expected
outputs are shown so you can verify before moving on.

## Pre-flight checklist

- [ ] `glab auth status` — correct account is active
- [ ] `snow connection test --connection local-oauth` — succeeds
- [ ] CoCo plugin installed: `cortex plugin list | grep devops-coco-agents`
- [ ] Snowflake account identifier ready (e.g. `xy12345.us-east-1`)

## Start the scaffold

Type in the CoCo chat panel:

```text
$devops-coco-agents:scaffold-for-gitlab
```

The skill asks: **Quick start or Full setup?** Choose Quick start for a 10-minute run,
Full setup to also run the smoke test and walk through the smart-fix verification.

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

```text
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
No password stored — GitLab issues a short-lived token that Snowflake verifies directly.

---

## Step 4 — Configure

The skill collects the bot token (needed to create MRs and issues):

```text
Use your glab auth token (convenient)
  OR
Use a dedicated long-lived PAT (api + write_repository scopes)
```

Then sets 7 CI/CD variables:

| Variable | Masked |
|----------|--------|
| `SNOWFLAKE_ACCOUNT` | yes |
| `SNOWFLAKE_USER` | no |
| `SNOWFLAKE_WAREHOUSE` | no |
| `SNOWFLAKE_ROLE` | no |
| `GITLAB_TOKEN_COCO` | yes |
| `COCO_MAX_AUTO` | no (value: `conservative`) |

**Quick start path:** after variables are set, CoCo re-enables pipelines and applies
branch protection (push restricted to MRs). Done.

**Full setup path:** also offers the smoke test below.

---

## Step 5 — Watch the Loop (full setup only)

CoCo asks which demo app type to generate (DE / Streamlit / Custom), shows a
generation prompt for confirmation, then writes the files directly into `demo/`
using its Write tool. Pipelines are enabled and the commit is pushed.

### What the scan finds

| Issue | Severity | Routing (conservative) |
|-------|----------|----------------------|
| `FALLBACK_DB_CONN = "dev-placeholder-replace-before-deploy"` | low | **auto-fix** |
| `f"SELECT * FROM {table_name} WHERE amount > 0"` | high | **needs-review** |
| `subprocess.run(f"snow sql -q '{cmd}'", shell=True)` | critical | **needs-review** |

### Beat 1 — Ceiling source

Check the scan-code job log for the active ceiling:

```bash
glab pipeline list --project ksampath/nimble-proxy 2>&1 | head -3
```

Look for this line in the job output:

```
Fix ceiling: conservative (source: .gitlab/coco-config.yml)
```

### Beat 2 — Auto-fix MR (low severity)

```bash
glab issue list --label "coco:auto-fix"
glab mr list --state opened
```

Expected: 1 issue labeled `coco:auto-fix`, 1 open MR fixing the `FALLBACK_DB_CONN` placeholder.

### Beat 3 — Needs-review labels (medium + high severity)

```bash
glab issue list --label "coco:needs-review"
```

Expected: 2 issues — f-string SQL injection (high/medium) + subprocess shell=True injection (critical/high).

### Beat 4 — Comment trigger (`@coco-agent fix`)

Trigger the fix on the SQL injection (f-string) needs-review issue via a note:

```bash
ENCODED_PATH="ksampath%2Fnimble-proxy"
ISSUE_IID=$(glab issue list --label "coco:needs-review" -P 1 \
  | python3 -c "
import sys
for line in sys.stdin:
    if 'sql' in line.lower() or 'select' in line.lower() or 'inject' in line.lower():
        print(line.split()[0].lstrip('#'))
        break
")
glab api "projects/$ENCODED_PATH/issues/$ISSUE_IID/notes" \
  -X POST -F "body=@coco-agent fix"
```

Watch the comment-fix pipeline job trigger:

```bash
glab pipeline list --project ksampath/nimble-proxy 2>&1 | head -5
```

Expected: fix job fires, MR raised for the logging issue within ~2 minutes.

---

## Step 6 — Clean Up (optional)

- **Yes, tear down everything** — drops Snowflake objects, deletes project
- **Drop Snowflake only** — keeps the project
- **Keep everything**

**Verify after full teardown:**

```bash
glab api "projects/ksampath%2Fnimble-proxy" 2>&1          # should 404
snow sql -q "SHOW USERS LIKE 'DEMO_GL_%_COCO_AGENT_USER';"  # 0 rows
```
