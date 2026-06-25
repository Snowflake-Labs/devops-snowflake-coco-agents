# Step 6a: Teardown Snowflake + Runner (GitLab)

> Sub-step of Step 6. Executes after user confirms teardown.
> Read manifest values from step-6 router before loading this sub-step.

**Disable pipelines:**

```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
```

Load `shared/snowflake-drop-sql.md` and execute guard + DROP with values:

- `$SF_USER`, `$SF_WH`, `$SF_ROLE` from manifest

```bash
# No PAT to revoke — OIDC-only auth since Jun 16 cleanup
```
