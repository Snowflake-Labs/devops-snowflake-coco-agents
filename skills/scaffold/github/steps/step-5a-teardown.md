# Step 6a: Teardown Snowflake + Runner (GitHub)

> Sub-step of Step 6. Executes after user confirms teardown.
> Read manifest values from step-6 router before loading this sub-step.

**Disable Actions:**

```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'
```

Load `shared/snowflake-drop-sql.md` and execute guard + DROP with values:

- `$SF_USER`, `$SF_WH`, `$SF_ROLE` from manifest

```bash
# No PAT to revoke — OIDC-only auth since Jun 16 cleanup
```
