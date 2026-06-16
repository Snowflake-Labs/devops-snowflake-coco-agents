# Reference: glab API Patterns

## Auth Pre-flight

`glab api` commands automatically use the session from `glab auth login`.
Always verify before starting:

```bash
glab auth status 2>&1
```

If output does NOT contain `"Logged in to gitlab.com"`:
> ⚠️ **STOP:** Run `glab auth login` and re-invoke the skill.

Get the stored token (for setting as CI/CD variable `GITLAB_TOKEN_COCO`):

```bash
GITLAB_TOKEN_COCO=$(glab auth token)
```

⚠️ `glab auth token` returns your personal OAuth token. Fine for
development/testing. For long-lived CI bots, create a dedicated Project Access
Token with `api`, `write_repository`, and `ai_features` scopes.
See `skills/scaffold/references/token-scopes.md`.

---

## Variables API — 403 When Builds Disabled

The GitLab variables API (`/projects/:id/variables`) returns 403 when
`builds_access_level=disabled`. Additionally, `glab api` sends
`PRIVATE-TOKEN` header; OAuth tokens require `Authorization: Bearer`.

Always use `curl` for variable operations and temporarily set builds to
`private` before writing:

```bash
GLAB_BASE="https://gitlab.com/api/v4/projects/$ENCODED_PATH"

# Temporarily enable (variables API returns 403 when disabled)
curl -sf -X PUT "https://gitlab.com/api/v4/projects/$ENCODED_PATH" \
  -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
  -F "builds_access_level=private" -o /dev/null

# Set variable
curl -sf -X POST "$GLAB_BASE/variables" \
  -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
  -F "key=MY_VAR" -F "value=hello" -F "masked=false" -o /dev/null

# Restore disabled
curl -sf -X PUT "https://gitlab.com/api/v4/projects/$ENCODED_PATH" \
  -H "Authorization: Bearer $GITLAB_TOKEN_COCO" \
  -F "builds_access_level=disabled" -o /dev/null
```

Note: `glab api PUT /projects/:id` (project settings, not variables) works
fine even when builds are disabled — only the `/variables` endpoint is blocked.

---

## JSON Output Parsing (`_j` helper)

`glab api` has no `--jq` flag. Define `_j` once at the top of any bash block
that needs to extract fields from JSON output:

```bash
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

**Simple key extraction:**

```bash
USERNAME=$(glab api user | _j "['username']")
BUILDS=$(glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']")
```

**Namespace ID (personal namespace — not the same as user ID):**

```bash
NAMESPACE_ID=$(glab api "namespaces?search=$GITLAB_USER" \
  | python3 -c "import sys,json; ns=[n for n in json.load(sys.stdin) if n['kind']=='user']; print(ns[0]['id'])")
```

**Complex list-filtering — keep inline python3** (too verbose for `_j`):

## Common One-Liners

```bash
# Encode project path for URL
ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")

# Check builds_access_level
glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"
# Expected values: "enabled" | "disabled" | "private"

# Disable / enable pipelines (project settings endpoint — works even when disabled)
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled
```
