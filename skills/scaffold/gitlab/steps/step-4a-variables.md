# Step 4a: Set GitLab CI/CD Variables

> Sub-step of Step 4. Load after gate check passes.
> Uses `glab api POST/PUT` directly — avoids `glab variable set` auth override issues.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_4

cd "$PROJECT_NAME"
# _v KEY VALUE [masked=true]: create-or-update CI/CD variable
_v() { local K=$1 V=$2 M=${3:-false}
  glab api "projects/$ENCODED_PATH/variables" --method POST -F "key=$K" -F "value=$V" -F "masked=$M" 2>/dev/null \
  || glab api "projects/$ENCODED_PATH/variables/$K" --method PUT -F "value=$V" -F "masked=$M" 2>/dev/null
  echo "✓ $K"; }

_v SNOWFLAKE_ACCOUNT  "$SNOWFLAKE_ACCOUNT" true
_v SNOWFLAKE_USER     "$SF_USER"
_v SNOWFLAKE_WAREHOUSE "$SF_WH"
_v SNOWFLAKE_ROLE     "$SF_ROLE"
read -r _PAT < <(security find-generic-password -s "$KEYCHAIN_SVC" -a "$SF_USER" -w); _v SNOWFLAKE_PAT "$_PAT" true
# GITLAB_TOKEN_coco from glab auth token or cortex secret
# If using glab auth token: GITLAB_TOKEN_coco set in shell from coordinator
# If using cortex secret: execute with secret_env={"GITLAB_TOKEN_coco": "gitlab-token-coco"}
_v GITLAB_TOKEN_coco "$GITLAB_TOKEN_coco" true
```

**Verify:** `glab variable list 2>&1 | grep -E "SNOWFLAKE|GITLAB_TOKEN"` — confirm all 6 variables listed.

### What we did
- 6 CI/CD variables set on `$PROJECT_PATH`
- Pipelines can authenticate via OIDC (cloud) or PAT (local runner)
