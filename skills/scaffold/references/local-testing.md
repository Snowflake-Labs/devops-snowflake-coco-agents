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

## Option 2 — GitLab: project-local registered runner (shell executor)

**What this tests:** The full `.gitlab-ci.yml` pipeline — real GitLab OIDC token
issuance, `include:` directives processed, `rules:` evaluated. Identical to what
runs on shared runners. The shell executor uses the local `cortex` binary on PATH
directly — no Docker image build needed.

**Auth:** GitLab issues a real OIDC token to registered runners. No PAT is needed
if Beat 3 (Snowflake OIDC user) is complete.

**Note:** The scaffold skill (Beat 4) can set this up for you automatically.
These steps are the manual equivalent.

### Setup

```bash
# Download the runner binary into the project
mkdir -p .gitlab/runner
RUNNER_VERSION=$(curl -s \
  "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab-runner/releases/permalink/latest" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://gitlab-runner-downloads.s3.amazonaws.com/v${RUNNER_VERSION}/binaries/gitlab-runner-darwin-arm64" \
  -o .gitlab/runner/gitlab-runner
chmod +x .gitlab/runner/gitlab-runner
echo '.gitlab/runner/' >> .gitignore

# Create a runner token via GitLab API
ENCODED_PATH=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1],safe=''))" "$PROJECT_PATH")
PROJECT_ID=$(glab api "projects/$ENCODED_PATH" --jq .id)
RUNNER_TOKEN=$(glab api "user/runners" -X POST \
  --field "runner_type=project_type" \
  --field "project_id=$PROJECT_ID" \
  --field "tag_list=local" \
  --field "run_untagged=false" \
  --field "description=local-mac" \
  --jq .token)

# Register with project-local config
.gitlab/runner/gitlab-runner register \
  --config .gitlab/runner/config.toml \
  --url https://gitlab.com \
  --token "$RUNNER_TOKEN" \
  --executor shell \
  --non-interactive
```

### Patch pipeline to use the local runner

```bash
python3 - << 'PYEOF'
import re
content = open(".gitlab-ci.yml").read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)", rf"\1\n  tags: [local]", content, flags=re.MULTILINE)
open(".gitlab-ci.yml", "w").write(content)
print("Patched: tags: [local] added")
PYEOF
git add .gitlab-ci.yml && git commit -m "ci: use self-hosted local runner for testing [skip ci]"
git push
```

### Start the runner

```bash
.gitlab/runner/gitlab-runner run --config .gitlab/runner/config.toml
```

Keep this running in a terminal. Push to `demo/` or push the pipeline trigger commit
and the `scan-code` job will be picked up by the local runner.

### Check results

```bash
glab issue list --label coco-agent
glab mr list --state opened
```

> **Legacy fallback:** `gitlab-runner exec docker scan-code --env ... --docker-image ...`
> still works for a quick single-job script check (no `include:` processing, no OIDC)
> but is deprecated since GitLab 16+.

---

## Option 3 — GitHub: project-local self-hosted runner

**What this tests:** The full `cortex-scan.yml` / `cortex-fix.yml` workflow YAML,
including real GitHub OIDC token issuance.

**Auth:** GitHub issues a real OIDC token to the self-hosted runner.
`snowflake-cli-action` exchanges it for a Snowflake session. No PAT needed.

**Requirement:** Beat 3 (Snowflake OIDC user) must be complete.

**Note:** The scaffold skill (Beat 4) sets this up automatically.
These steps are the manual equivalent.

### Setup

```bash
mkdir -p .github/runner
echo '.github/runner/' >> .gitignore
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz" \
  | tar xz -C .github/runner
RUNNER_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/registration-token" -X POST -q .token)
.github/runner/config.sh \
  --url "https://github.com/$REPO_PATH" \
  --token "$RUNNER_TOKEN" \
  --labels "self-hosted,local" \
  --unattended
```

### Patch workflows to use the local runner

```bash
sed -i '' 's/runs-on: ubuntu-latest/runs-on: [self-hosted, local]/g' \
  .github/workflows/cortex-scan.yml \
  .github/workflows/cortex-fix.yml
git add .github/workflows/ && git commit -m "ci(workflows): use self-hosted local runner [skip ci]"
git push
```

### Start the runner

```bash
.github/runner/run.sh
```

Keep this running. Push to `demo/` and the scan workflow will be picked up locally.

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
| Test full GitLab pipeline with real OIDC | Option 2 |
| Test real GitHub workflow YAML with OIDC | Option 3 |
| Beat 3 not done yet | Option 1 (no OIDC required) |
