# Local Testing Playbook

A reference for testing the scan→issue→fix loop locally before or without a
hosted CI runner. Load this from Beat 5 of the scaffold skills when the user
asks about local or pre-CI testing.

Three options, simplest first. Start at Option 1.

---

## Prerequisites (all options)

- Local `cortex` binary on PATH (set by `.envrc` in this workspace:
  `coco-0.26.613+.../cortex`)
- `gh` authenticated: `gh auth status`
- Snowflake WORKLOAD_IDENTITY user provisioned (Beat 3 complete)

---

## Option 1 — Run `cortex exec` directly (zero setup)

**What this tests:** The entire AI scan/fix logic and the `gh issue create` calls,
end-to-end. No CI runner, no Docker. Proves the loop works in under 5 minutes.

**Auth:** Uses your local `~/.snowflake/connections.toml` — any valid Snowflake
connection (key-pair, `externalbrowser`, or an existing profile). OIDC is not
required here because you are not going through GitHub Actions.

### Run the scan

```bash
cd /path/to/your-scaffolded-repo

cortex exec --file .cortex/prompts/scan.md \
  -c default --bypass --no-history \
  --allowed "Read" --allowed "Bash(gh issue create *)"
```

CoCo reads `demo/`, finds the intentional issues, and calls `gh issue create`
directly. Issues appear on the remote within seconds.

### Run the fix (manually trigger)

After a `[coco-agent]` issue exists, test the fix prompt:

```bash
export ISSUE_TITLE="[coco-agent] Fix hardcoded schema in app.py"
export ISSUE_BODY="SCHEMA = 'PUBLIC' is hardcoded — should come from an env var."

envsubst < .cortex/prompts/fix.md \
  | cortex exec --file - \
    -c default --bypass --no-history \
    --allowed "Read" --allowed "Edit" --allowed "Write" \
    --allowed "Bash(git *)" --allowed "Bash(gh *)"
```

---

## Option 2 — GitLab: local `gitlab-runner` (no pipeline changes needed)

**What this tests:** The full `.gitlab-ci.yml` job script — same env var handling,
same Docker image, same shell logic as real CI.

**Auth:** The `.gitlab-ci.yml` already supports a `SNOWFLAKE_PAT` env-var override
for local testing (set `SNOWFLAKE_PAT` to bypass OIDC). This is intentional in
the GitLab template and pre-dates the changes in this plugin.

### Setup

```bash
brew install gitlab-runner   # macOS; also available via apt/dnf

# Build the cortex-code-agent image locally
cd /path/to/your-gitlab-project
docker build -t cortex-code-agent:latest .
```

### Run the scan job

```bash
gitlab-runner exec docker scan-code \
  --env SNOWFLAKE_ACCOUNT=xy12345.us-east-1 \
  --env SNOWFLAKE_USER=DEMO_GITLAB_COCO_AGENT_USER \
  --env SNOWFLAKE_WAREHOUSE=DEMO_GITLAB_COCO_AGENT_WH \
  --env SNOWFLAKE_ROLE=DEMO_GITLAB_COCO_AGENT_ROLE \
  --env SNOWFLAKE_PAT=v2:... \
  --env GITLAB_TOKEN_coco=glpat-... \
  --env GITLAB_HOST=gitlab.com \
  --env CI_PROJECT_PATH=mygroup/my-coco-agent \
  --docker-image cortex-code-agent:latest
```

> `gitlab-runner exec docker` is deprecated since GitLab 16+ but still works for
> local testing.

---

## Option 3 — GitHub: self-hosted runner on your Mac

**What this tests:** The full `cortex-scan.yml` / `cortex-fix.yml` workflow YAML,
including real GitHub OIDC token issuance. This is the most complete test because
it runs the actual workflow — not a simulation.

**Auth:** GitHub issues a real OIDC token to the self-hosted runner. The
`snowflake-cli-action` step exchanges it for a Snowflake session exactly as it
would in production. No PAT is needed.

**Requirement:** Beat 3 (Snowflake OIDC user provisioning) must be complete.

### Register your Mac as a self-hosted runner

```bash
# Via gh CLI (run from inside your scaffolded repo):
gh api "repos/$REPO_PATH/actions/runners/registration-token" \
  -X POST -q .token | xargs -I{} \
  ~/actions-runner/config.sh \
    --url "https://github.com/$REPO_PATH" \
    --token {} \
    --labels "self-hosted,macOS" \
    --unattended

# Or follow the UI path:
# Settings → Actions → Runners → New self-hosted runner → macOS
```

If you don't have the runner package yet:
```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -LsS https://github.com/actions/runner/releases/latest/download/actions-runner-osx-arm64-2.321.0.tar.gz | tar xz
```
Check https://github.com/actions/runner/releases for the current version.

### Start the runner

```bash
~/actions-runner/run.sh
```

Keep this running in a terminal while you test.

### Trigger the scan workflow

Push any change to `demo/` on `main`:

```bash
cd /path/to/your-scaffolded-repo
git commit --allow-empty -m "test(smoke): trigger local scan run"
git push
```

Or trigger manually:
```bash
gh workflow run cortex-scan.yml --ref main
```

The workflow runs on your Mac. The `Install cortex` step is skipped because the
local binary already has `exec`. Issues appear in the GitHub repo as normal.

### Check results

```bash
gh issue list --repo "$REPO_PATH" --label coco-agent
gh pr list   --repo "$REPO_PATH" --state open
```

---

## Choosing an option

| Goal | Use |
|------|-----|
| Prove CoCo logic works, fastest feedback | Option 1 |
| Test full GitLab pipeline scripts locally | Option 2 |
| Test real GitHub workflow YAML with OIDC end-to-end | Option 3 |
| Beat 3 not done yet | Option 1 (no OIDC required) |
