# Reference: glab API Patterns

## Auth Pre-flight

`glab api` commands automatically use the session from `glab auth login`.
Always verify before starting:

```bash
glab auth status 2>&1
```

If output does NOT contain `"Logged in to gitlab.com"`:
> ⚠️ **STOP:** Run `glab auth login` and re-invoke the skill.

Get the stored token (for setting as a CI/CD variable):
```bash
GITLAB_TOKEN_coco=$(glab auth token)
```

⚠️ `glab auth token` returns your personal OAuth token. Fine for
development/testing. For long-lived CI bots shared across a team, create a
dedicated Project Access Token with `api` + `write_repository` scopes instead.

---

## JSON Output Parsing (`_j` helper)

`glab api` has no `--jq` flag. Define `_j` once at the top of any bash block
that needs to extract fields from JSON output:

```bash
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

**Simple key extraction:**
```bash
NAMESPACE_ID=$(glab api user | _j "['id']")
USERNAME=$(glab api user | _j "['username']")
BUILDS=$(glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']")
RUNNER_TOKEN=$(glab api "projects/$ENCODED_PATH/runners" \
  --method POST -F runner_type=project_type | _j "['token']")
```

**Verify a single field:**
```bash
glab api "projects/$ENCODED_PATH" | _j "['visibility']"
```

**Complex list-filtering — keep inline python3** (too verbose for `_j`):
```bash
RUNNER_ID=$(glab api "projects/$ENCODED_PATH/runners" \
  | python3 -c "import sys,json; r=[x for x in json.load(sys.stdin) \
    if x.get('description')=='local-mac']; print(r[0]['id'] if r else '')")
```

---

## Common One-Liners

```bash
# Encode project path for URL
ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")

# Get current user's namespace ID
NAMESPACE_ID=$(glab api user | _j "['id']")

# Check builds_access_level
glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"
# Expected values: "enabled" | "disabled" | "private"

# Disable / enable pipelines
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled
```
