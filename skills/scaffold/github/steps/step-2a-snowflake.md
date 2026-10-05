# Step 3a: Create Snowflake Objects (GitHub)

> Sub-step of Step 3.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_2
python3 "$MANIFEST_OPS" fill-snowflake \
  --manifest "$MANIFEST" --prefix "$PREFIX" --repo-name "$REPO_NAME" --platform "github"
SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
# Persist the subject confirmed in Step 2 so resume and re-runs reuse it
python3 "$MANIFEST_OPS" fill-oidc --manifest "$MANIFEST" --subject "$OIDC_SUBJECT"
```

Load `shared/snowflake-setup-sql.md` and execute with:

- `$OIDC_ISSUER` = `https://token.actions.githubusercontent.com`
- `$OIDC_SUBJECT` = the value confirmed in Step 2 (immutable `repo:<owner>@<owner_id>/<repo>@<repo_id>:ref:refs/heads/main` for new repos)

**Post-step verification** (`snowflake_sql_execute`):

```sql
SHOW ROLES LIKE '$SF_ROLE';
```

```sql
SHOW WAREHOUSES LIKE '$SF_WH';
```

If empty or error: ⚠️ Re-run this step.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_2
```

### What we did

- Role `$SF_ROLE`, warehouse `$SF_WH`, service user `$SF_USER` created
- OIDC auth bound to `$OIDC_SUBJECT` (saved as `snowflake.oidc_subject` in the manifest)
- If the repo is later renamed or transferred, the subject changes — re-run
  `ALTER USER $SF_USER SET WORKLOAD_IDENTITY` with the new value
- Object names persisted in manifest `[snowflake]` section
