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

Also read and display `$REPO_NAME/snowflake/setup.sql` with variables substituted so the user can review the exact SQL before confirming.

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_3

snow sql -f "$REPO_NAME/snowflake/setup.sql" \
  -D "PREFIX=$PREFIX" \
  -D "REPO_PATH=$REPO_PATH"
```

**Post-step verification:**
```bash
snow sql -q "DESC USER ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_USER" --format json 2>&1
snow sql -q "SHOW ROLES LIKE '${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_ROLE'" --format json 2>&1
snow sql -q "SHOW WAREHOUSES LIKE '${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_WH'" --format json 2>&1
```
If any return empty or error:
> ⚠️ **Gate check failed:** OIDC user not found after provisioning. Re-run this step.

```bash
python3 "$MANIFEST_OPS" fill-snowflake \
  --manifest "$MANIFEST" --prefix "$PREFIX" --repo-name "$REPO_NAME" --platform "github"

python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_3
```

### What we did
- Role, warehouse, and `SERVICE` user with `WORKLOAD_IDENTITY` OIDC config created
- Subject claim bound to `repo:$REPO_PATH:ref:refs/heads/main`
- Snowflake object names persisted in manifest `[snowflake]` section
