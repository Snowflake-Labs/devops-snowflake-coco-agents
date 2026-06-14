# Step 4a: Set GitHub Secrets + Workflow Permissions

> Sub-step of Step 4. Load after gate check passes.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_4

gh secret set SNOWFLAKE_ACCOUNT   --repo "$REPO_PATH" --body "$SNOWFLAKE_ACCOUNT"
gh secret set SNOWFLAKE_ROLE      --repo "$REPO_PATH" --body "$SF_ROLE"
gh secret set SNOWFLAKE_WAREHOUSE --repo "$REPO_PATH" --body "$SF_WH"
gh secret set SNOWFLAKE_USER      --repo "$REPO_PATH" --body "$SF_USER"
gh secret set SNOWFLAKE_PAT       --repo "$REPO_PATH" --body "$SNOWFLAKE_PAT"

# Allow Actions to create PRs (required for cortex-fix.yml)
gh api "repos/$REPO_PATH/actions/permissions/workflow" \
  -X PUT \
  --field default_workflow_permissions=write \
  --field can_approve_pull_request_reviews=true
```

**Verify:**
```bash
gh secret list --repo "$REPO_PATH" 2>&1
gh api "repos/$REPO_PATH/actions/permissions/workflow" \
  --jq '{permissions: .default_workflow_permissions, can_create_pr: .can_approve_pull_request_reviews}'
```
Confirm 5 secrets listed and `can_create_pr: true`.

### What we did
- 5 secrets set on `$REPO_PATH` (Snowflake context + local runner identity)
- Workflow permissions: Actions can create PRs, write token is default
