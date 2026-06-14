# Step 3: Connect Snowflake

> Part of the GitHub scaffold skill. Load when executing Step 3.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

**Gate check (staleness-aware):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_2 \
  || gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```
If enabled is `true`:
> ⚠️ **Gate check failed:** Actions are still enabled. Complete Step 2 first.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> See `references/manifest.md` (## Connect Snowflake — OIDC Explanation).
> GitHub: "the Actions runner proves its identity". GitLab: "the CI job proves its identity".

**What we'll do**

| Object | Value |
|--------|-------|
| Role | `${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_ROLE` |
| Warehouse | `${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_USER` (TYPE = SERVICE) |
| Auth | `WORKLOAD_IDENTITY = (TYPE = OIDC ISSUER = https://token.actions.githubusercontent.com)` |
| Subject | `repo:$REPO_PATH:ref:refs/heads/main` |

Also show the exact SQL that will run (generated from manifest values) so the user can review before confirming.

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_3

# Derive object names first — must happen before SQL execution
python3 "$MANIFEST_OPS" fill-snowflake \
  --manifest "$MANIFEST" --prefix "$PREFIX" --repo-name "$REPO_NAME" --platform "github"

SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)

snow sql -q "
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS $SF_ROLE;
GRANT ROLE $SF_ROLE TO ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS $SF_WH
  WAREHOUSE_SIZE = 'X-SMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
GRANT USAGE ON WAREHOUSE $SF_WH TO ROLE $SF_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE $SF_ROLE;
CREATE USER IF NOT EXISTS $SF_USER
  TYPE = SERVICE DEFAULT_ROLE = $SF_ROLE DEFAULT_WAREHOUSE = $SF_WH;
GRANT ROLE $SF_ROLE TO USER $SF_USER;
ALTER USER $SF_USER SET
  WORKLOAD_IDENTITY = (
    TYPE = OIDC
    ISSUER = 'https://token.actions.githubusercontent.com'
    SUBJECT = 'repo:$REPO_PATH:ref:refs/heads/main'
  );
"
```

**Post-step verification:**
```bash
snow sql -q "DESC USER $SF_USER" --format json 2>&1
snow sql -q "SHOW ROLES LIKE '$SF_ROLE'" --format json 2>&1
snow sql -q "SHOW WAREHOUSES LIKE '$SF_WH'" --format json 2>&1
```
If any return empty or error:
> ⚠️ **Gate check failed:** OIDC user not found after provisioning. Re-run this step.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_3
```

### What we did
- Role, warehouse, and `SERVICE` user with `WORKLOAD_IDENTITY` OIDC config created
- Subject claim bound to `repo:$REPO_PATH:ref:refs/heads/main`
- Snowflake object names persisted in manifest `[snowflake]` section
