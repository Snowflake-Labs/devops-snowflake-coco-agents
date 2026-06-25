# Step 4a: Set GitHub Secrets

> Sub-step of Step 4. Load after gate check passes.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_2

gh secret set SNOWFLAKE_ACCOUNT   --repo "$REPO_PATH" --body "$SNOWFLAKE_ACCOUNT"
gh secret set SNOWFLAKE_ROLE      --repo "$REPO_PATH" --body "$SF_ROLE"
gh secret set SNOWFLAKE_WAREHOUSE --repo "$REPO_PATH" --body "$SF_WH"
gh secret set SNOWFLAKE_USER      --repo "$REPO_PATH" --body "$SF_USER"

# Fix ceiling — repository variable (not a secret; visible in logs)
gh variable set COCO_MAX_AUTO --repo "$REPO_PATH" --body "conservative"
```

**Verify:**

```bash
gh secret list --repo "$REPO_PATH" 2>&1
```

Confirm 4 secrets listed.

### What we did

- 4 secrets set on `$REPO_PATH` (Snowflake context via OIDC)
- Fix ceiling variable set to `conservative`
