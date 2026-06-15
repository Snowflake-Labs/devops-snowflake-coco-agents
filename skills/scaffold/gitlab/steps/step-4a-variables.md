# Step 4a: Set GitLab CI/CD Variables

> Sub-step of Step 4. Load after gate check passes.
> Uses `glab api POST/PUT` directly — avoids `glab variable set` auth override issues.

**Collect bot token** (`GITLAB_TOKEN_coco` — needed to set the CI/CD variable):
```bash
glab auth status 2>&1 | grep "Logged in"
```
If authenticated, ask:
```
ask_user_question:
  header: "Bot token"
  question: "Use your glab auth token as the CI pipeline bot token, or provide a dedicated PAT?"
  options:
    - label: "Use glab auth token (convenient)"
      description: "Extracts the token glab already has — no extra setup"
    - label: "Use a dedicated long-lived PAT"
      description: "Better for shared projects or CI that outlives your session"
```
If "Use glab auth token": `GITLAB_TOKEN_coco=$(glab auth token)`
> ⚠️ Personal OAuth token — if you run `glab auth logout`, the pipeline loses access.

If "Use dedicated PAT":
Open `https://gitlab.com/-/user_settings/personal_access_tokens?name=coco-bot&scopes=api,write_repository`
then: `cortex secret store gitlab-token-coco --prompt`
Use with `secret_env: {"GITLAB_TOKEN_coco": "gitlab-token-coco"}` when executing the `_v` block below.

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
# Fix ceiling — CI/CD variable (not masked; visible in job logs for auditability)
_v COCO_MAX_AUTO "conservative" false
# GITLAB_TOKEN_coco from glab auth token or cortex secret
# If using glab auth token: GITLAB_TOKEN_coco set in shell from coordinator
# If using cortex secret: execute with secret_env={"GITLAB_TOKEN_coco": "gitlab-token-coco"}
_v GITLAB_TOKEN_coco "$GITLAB_TOKEN_coco" true
```

**Verify:** `glab api "projects/$ENCODED_PATH/variables" | python3 -c "import sys,json; [print(v['key']) for v in json.load(sys.stdin)]"` — confirm all 6 keys listed.

### What we did
- 6 CI/CD variables set on `$PROJECT_PATH`
- Pipelines can authenticate via OIDC (cloud) or PAT (local runner)
