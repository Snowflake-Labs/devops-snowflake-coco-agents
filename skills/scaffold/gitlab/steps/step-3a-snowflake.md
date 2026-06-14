# Step 3a: Create Snowflake Objects (GitLab)

> Sub-step of Step 3.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_3
python3 "$MANIFEST_OPS" fill-snowflake \
  --manifest "$MANIFEST" --prefix "$PREFIX" --repo-name "$PROJECT_NAME" --platform "gitlab"
SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
```

Load `shared/snowflake-setup-sql.md` and execute with:
- `$OIDC_ISSUER` = `https://gitlab.com`
- `$OIDC_SUBJECT` = `project_path:$PROJECT_PATH:ref_type:branch:ref:main`

**Post-step verification** (`snowflake_sql_execute`):
```sql
SHOW ROLES LIKE '$SF_ROLE';
```
```sql
SHOW WAREHOUSES LIKE '$SF_WH';
```
If empty or error: ⚠️ Re-run this step.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_3
```

### What we did
- Role `$SF_ROLE`, warehouse `$SF_WH`, service user `$SF_USER` created
- OIDC auth bound to `project_path:$PROJECT_PATH:ref_type:branch:ref:main`
- Object names persisted in manifest `[snowflake]` section
