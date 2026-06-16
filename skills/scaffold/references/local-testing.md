# Local Testing Playbook

A reference for testing the scan→issue→fix loop locally without CI.
Load this when the user asks about local or pre-CI testing.

---

## Prerequisites

- `cortex exec` on PATH — beta channel, version `1.1.9+204229.0400c522997b` or later
- `gh` or `glab` authenticated
- Snowflake connection configured in `~/.snowflake/connections.toml`
- Snowflake WORKLOAD_IDENTITY user provisioned (Step 3 complete)

---

## Run `cortex exec` directly (zero setup)

**What this tests:** The entire AI scan/fix logic end-to-end. No CI runner, no Docker.
Proves the loop works in under 5 minutes.

**Auth:** Uses your local `~/.snowflake/connections.toml` — any valid connection
(`externalbrowser`, `OAUTH_AUTHORIZATION_CODE`, key-pair). OIDC is not required
because you are not going through GitHub Actions or GitLab CI.

### Run the scan

```bash
cd /path/to/your-scaffolded-repo

# GitHub
cortex exec --file .cortex/prompts/scan.md \
  -c default --bypass --no-history \
  --allowed "Glob" --allowed "Read" \
  --allowed "Bash(gh issue create *)" --allowed "Bash(gh label create *)"

# GitLab
cortex exec --file .cortex/prompts/scan.md \
  -c default --bypass --no-history \
  --allowed "Glob" --allowed "Read" \
  --allowed "Bash(glab issue create *)" --allowed "Bash(glab label create *)"
```

CoCo discovers Python files, scores each finding, and creates issues on the remote
within seconds.

### Run the fix (manually trigger)

After a `[coco-agent]` issue exists:

```bash
export ISSUE_NUMBER=1
export ISSUE_TITLE="[coco-agent] Bug: hardcoded schema in app.py"
export ISSUE_BODY="SCHEMA = 'PUBLIC' is hardcoded — should come from an env var."

# GitHub
envsubst < .cortex/prompts/fix.md \
  | cortex exec --file - \
    -c default --bypass --no-history \
    --allowed "Read" --allowed "Edit" --allowed "Write" \
    --allowed "Bash(git *)" --allowed "Bash(gh *)"

# GitLab
envsubst < .cortex/prompts/fix.md \
  | cortex exec --file - \
    -c default --bypass --no-history \
    --allowed "Read" --allowed "Edit" --allowed "Write" \
    --allowed "Bash(git *)" --allowed "Bash(glab *)"
```

### Verify

```bash
# GitHub
gh issue list --label coco-agent
gh pr list --state open

# GitLab
glab issue list --label coco-agent
glab mr list --state opened
```
