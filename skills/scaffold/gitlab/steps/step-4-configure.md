# Step 4: Configure

> Part of the GitLab scaffold skill. Load when executing Step 4.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
```

**Gate check (staleness-aware):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_3 \
  || snow sql -q "DESC USER $SF_USER" --format json 2>&1
```
If empty or error:
> ⚠️ **Gate check failed:** OIDC user not found. Complete Step 3 first.

---

⚠️ MANDATORY: collect `GITLAB_TOKEN_coco` via `ask_user_question` (header: "GitLab token", type: text).
Before storing, validate the token has API access:
```bash
glab api user --token "$GITLAB_TOKEN_coco" --jq .username 2>&1
```
If empty/error: stop, ask user to generate a token with `api` scope.

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Six CI/CD variables: Snowflake auth context, local runner service-user PAT (no role creep), and GitLab bot token.

**What we'll do** — 6 CI/CD variables:
`SNOWFLAKE_ACCOUNT` (masked), `SNOWFLAKE_USER`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_PAT` (masked, local runner), `GITLAB_TOKEN_coco` (masked).

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_4

cd "$PROJECT_NAME"
glab variable set SNOWFLAKE_ACCOUNT   --value "$SNOWFLAKE_ACCOUNT"   --masked
glab variable set SNOWFLAKE_USER      --value "$SF_USER"
glab variable set SNOWFLAKE_WAREHOUSE --value "$SF_WH"
glab variable set SNOWFLAKE_ROLE      --value "$SF_ROLE"
glab variable set SNOWFLAKE_PAT       --value "$SNOWFLAKE_PAT"       --masked
glab variable set GITLAB_TOKEN_coco   --value "$GITLAB_TOKEN_coco"   --masked
```

**Post-step verification:**
```bash
glab variable list 2>&1
```
Confirm `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_PAT`, `GITLAB_TOKEN_coco` are listed.

### What we did
- 6 CI/CD variables set on `$PROJECT_PATH`
- Pipelines can authenticate to Snowflake via OIDC (cloud) or PAT (local runner)
- Bot authenticates via `GITLAB_TOKEN_coco`

---

## Optional: Local Runner Setup

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Local runner"
  question: "The pipelines run on a self-hosted local runner. Set one up for testing?"
  options:
    - label: "Yes, install runner inside the project"
      description: "Installs to .gitlab/runner/ — isolated per project, gitignored"
    - label: "Skip — use GitLab.com shared runners"
    - label: "Stop here"
```

If "Skip": mark step complete and move on.

If "Yes":

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> A project-local runner lets you test the full loop before committing to
> shared runners. Shell executor — no Docker required.

**What we'll do**
```
Installs:  $PROJECT_NAME/.gitlab/runner/  (gitignored, shell executor)
Tags:      [local]
Patches:   scan-code and coco-agent jobs get tags: [local]
```

Call `exit_plan_mode`. Then execute directly:

```bash
mkdir -p "$PROJECT_NAME/.gitlab/runner"
curl -LsS "https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-darwin-arm64" \
  -o "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
chmod +x "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
RUNNER_TOKEN=$(glab api "projects/$ENCODED_PATH/runners" \
  --method POST \
  --field "runner_type=project_type" \
  --field "description=local-mac" \
  --field "tag_list=local" \
  --jq .token)
"$PROJECT_NAME/.gitlab/runner/gitlab-runner" register \
  --non-interactive \
  --url "https://gitlab.com" \
  --token "$RUNNER_TOKEN" \
  --executor shell \
  --config "$PROJECT_NAME/.gitlab/runner/config.toml"

# Patch pipeline to add tags: [local] to scan-code and coco-agent jobs
python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)", rf"\1\n  tags: [local]", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Patched: tags: [local] added to scan-code and coco-agent")
PYEOF
git -C "$PROJECT_NAME" add .gitlab-ci.yml
git -C "$PROJECT_NAME" commit -m "ci: use self-hosted local runner for testing [skip ci]"

RUNNER_ID=$(glab api "projects/$ENCODED_PATH/runners" \
  --jq '.[] | select(.description == "local-mac") | .id' | head -1)

# Start runner in background — safe across chat steps
nohup "$PROJECT_NAME/.gitlab/runner/gitlab-runner" run \
  --config "$PROJECT_NAME/.gitlab/runner/config.toml" \
  > "$PROJECT_NAME/.gitlab/runner/runner.log" 2>&1 &
RUNNER_PID=$!
echo $RUNNER_PID > "$PROJECT_NAME/.gitlab/runner/runner.pid"
sleep 3
grep -q "Listening for Jobs" "$PROJECT_NAME/.gitlab/runner/runner.log" \
  && echo "✓ Runner is listening (PID $RUNNER_PID)" \
  || echo "Still starting — check: tail -f $PROJECT_NAME/.gitlab/runner/runner.log"

python3 "$MANIFEST_OPS" fill-runner \
  --manifest "$MANIFEST" --pid "$RUNNER_PID" --runner-id "$RUNNER_ID"
```

```
ask_user_question:
  header: "Start runner"
  question: "Runner started in background. Confirmed listening?"
  options:
    - label: "Yes, runner is listening — continue"
    - label: "Not yet — show runner log"
    - label: "Stop here"
```
If "Not yet": `tail -20 "$PROJECT_NAME/.gitlab/runner/runner.log"` and re-ask.

**Post-step verification:**
```bash
glab api "projects/$ENCODED_PATH/runners" \
  --jq '.[] | select(.description == "local-mac") | {id, status}'
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```

### What we did
- Runner installed in `$PROJECT_NAME/.gitlab/runner/` — PID `$RUNNER_PID` and ID `$RUNNER_ID` persisted in manifest
- Pipeline patched to add `tags: [local]` on `scan-code` and `coco-agent`

---

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Configure done"
  question: "Setup complete. Want to test with a sample app?"
  options:
    - label: "Yes, run smoke test and watch the loop"
      description: "Copies a 3-issue Python app into demo/, enables pipelines, commits and pushes"
    - label: "No, I'll push my own code later"
      description: "Skips smoke test — branch protection applied immediately"
    - label: "Stop here"
```

If "No, I'll push my own code later": protect main immediately:
```bash
glab api "projects/$ENCODED_PATH/protected_branches" \
  -X POST \
  -F name=main \
  -F push_access_level=0 \
  -F merge_access_level=40
```
