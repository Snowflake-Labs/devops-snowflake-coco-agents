# Step 3: Connect Snowflake

> Part of the GitLab scaffold skill. Load when executing Step 3.
> For SKILL_DIR resolution, see `references/manifest.md`.

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

**Gate check (staleness-aware):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_2 \
  || glab api "projects/$ENCODED_PATH" --jq .builds_access_level
```
If not `"disabled"`:
> ⚠️ **Gate check failed:** Pipelines are still enabled. Complete Step 2 first.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> WORKLOAD_IDENTITY replaces long-lived passwords with short-lived OIDC tokens.
> GitLab proves the job's identity; Snowflake verifies the issuer and subject
> claim. No secret is ever stored.
>
> `SNOWFLAKE.CORTEX_USER` database role is also granted — unlocks Cortex AI
> endpoints. Without it, every `cortex exec` call returns 403 Forbidden.

**What we'll do**

| Object | Value |
|--------|-------|
| Role | `${PREFIX}_GITLAB_COCO_AGENT_ROLE` |
| Warehouse | `${PREFIX}_GITLAB_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `${PREFIX}_GITLAB_COCO_AGENT_USER` (TYPE = SERVICE) |
| Auth | `WORKLOAD_IDENTITY = (TYPE = OIDC ISSUER = https://gitlab.com)` |
| Subject | `project_path:$PROJECT_PATH:ref_type:branch:ref:main` |

Also read and display `$PROJECT_NAME/snowflake/setup.sql` with variables substituted so the user can review before confirming.

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_3

snow sql -f "$PROJECT_NAME/snowflake/setup.sql" \
  -D "PREFIX=$PREFIX" \
  -D "REPO_PATH=$PROJECT_PATH" \
  --enable-templating STANDARD
```

**Post-step verification:**
```bash
snow sql -q "DESC USER ${PREFIX}_GITLAB_COCO_AGENT_USER" --format json 2>&1
snow sql -q "SHOW ROLES LIKE '${PREFIX}_GITLAB_COCO_AGENT_ROLE'" --format json 2>&1
snow sql -q "SHOW WAREHOUSES LIKE '${PREFIX}_GITLAB_COCO_AGENT_WH'" --format json 2>&1
```
If any return empty or error:
> ⚠️ **Gate check failed:** OIDC user not found after provisioning. Re-run this step.

```bash
python3 "$MANIFEST_OPS" fill-snowflake \
  --manifest "$MANIFEST" --prefix "$PREFIX" --platform "gitlab"

python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_3
```

### What we did
- Role, warehouse, and `SERVICE` user with `WORKLOAD_IDENTITY` OIDC config created
- Subject claim bound to `project_path:$PROJECT_PATH:ref_type:branch:ref:main`
- Snowflake object names persisted in manifest `[snowflake]` section
