# Step 4a: Set GitLab CI/CD Variables

> Sub-step of Step 4. Load after gate check passes.
> Uses `curl` directly — `glab api` returns 403 for the variables endpoint
> when `builds_access_level=disabled`. See `references/token-scopes.md`.

**Collect bot token:**

```bash
GITLAB_TOKEN_COCO=$(glab auth token)
```

> Token is used only to set CI/CD variables and is stored masked.
> For a long-lived dedicated PAT, create one with `api write_repository ai_features` scopes
> at `https://gitlab.com/-/user_settings/personal_access_tokens?name=coco-bot&scopes=api,write_repository,ai_features`

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_4

cd "$PROJECT_NAME"
GLAB_BASE="https://gitlab.com/api/v4/projects/$ENCODED_PATH"

# _v KEY VALUE [masked]: create-or-update CI/CD variable via curl Bearer auth
_v() { local K=$1 V=$2 M=${3:-false}
  curl -sf -X POST "$GLAB_BASE/variables" \
    -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
    -F "key=$K" -F "value=$V" -F "masked=$M" -o /dev/null \
  || curl -sf -X PUT "$GLAB_BASE/variables/$K" \
    -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
    -F "value=$V" -F "masked=$M" -o /dev/null
  echo "✓ $K"; }

# Variables API returns 403 when builds are disabled — temporarily enable
curl -sf -X PUT "https://gitlab.com/api/v4/projects/$ENCODED_PATH" \
  -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
  -F "builds_access_level=private" -o /dev/null

_v SNOWFLAKE_ACCOUNT   "$SNOWFLAKE_ACCOUNT" true
_v SNOWFLAKE_USER      "$SF_USER"
_v SNOWFLAKE_WAREHOUSE "$SF_WH"
_v SNOWFLAKE_ROLE      "$SF_ROLE"
_v COCO_MAX_AUTO       "conservative"
_v GITLAB_TOKEN_COCO   "$GITLAB_TOKEN_COCO" true
_v GITLAB_HOST         "gitlab.com"

# Restore disabled
curl -sf -X PUT "https://gitlab.com/api/v4/projects/$ENCODED_PATH" \
  -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
  -F "builds_access_level=disabled" -o /dev/null
echo "✓ Pipelines re-disabled"
```

**Verify:** `glab api "projects/$ENCODED_PATH/variables" | python3 -c "import sys,json; [print(v['key']) for v in json.load(sys.stdin)]"` — confirm 7 keys listed.

### What we did

- 7 CI/CD variables set on `$PROJECT_PATH`
- Pipelines remain disabled — re-enabled in Step 5 just before smoke test
