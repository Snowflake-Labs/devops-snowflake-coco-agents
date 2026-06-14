# Step 4: Configure

> Part of the GitHub scaffold skill. Load when executing Step 4.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
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

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Three Snowflake secrets tell the workflow which context to use.
> Two additional secrets pin the local runner to the service user (no role creep).
> Workflow permissions let Actions create PRs without a personal token.

**What we'll do**

| Secret | Value |
|--------|-------|
| `SNOWFLAKE_ACCOUNT` | `$SNOWFLAKE_ACCOUNT` |
| `SNOWFLAKE_ROLE` | `$SF_ROLE` |
| `SNOWFLAKE_WAREHOUSE` | `$SF_WH` |
| `SNOWFLAKE_USER` | `$SF_USER` (local runner only) |
| `SNOWFLAKE_PAT` | `$SNOWFLAKE_PAT` (local runner only) |
| Repo workflow permissions | `default_workflow_permissions=write`, `can_approve_pull_request_reviews=true` |

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_4

gh secret set SNOWFLAKE_ACCOUNT   --repo "$REPO_PATH" --body "$SNOWFLAKE_ACCOUNT"
gh secret set SNOWFLAKE_ROLE      --repo "$REPO_PATH" --body "$SF_ROLE"
gh secret set SNOWFLAKE_WAREHOUSE --repo "$REPO_PATH" --body "$SF_WH"
gh secret set SNOWFLAKE_USER      --repo "$REPO_PATH" --body "$SF_USER"
gh secret set SNOWFLAKE_PAT       --repo "$REPO_PATH" --body "$SNOWFLAKE_PAT"

# Allow Actions to create PRs (required for cortex-fix.yml to open fix PRs)
gh api "repos/$REPO_PATH/actions/permissions/workflow" \
  -X PUT \
  --field default_workflow_permissions=write \
  --field can_approve_pull_request_reviews=true
```

**Post-step verification:**
```bash
gh secret list --repo "$REPO_PATH" 2>&1
gh api "repos/$REPO_PATH/actions/permissions/workflow" --jq '{permissions: .default_workflow_permissions, can_create_pr: .can_approve_pull_request_reviews}'
```
Confirm all 5 secrets listed and `can_create_pr: true`.

### What we did
- 5 secrets set on `$REPO_PATH` (Snowflake context + local runner identity)
- Workflow permissions set: Actions can create PRs, write token is default

---

## Optional: Local Runner Setup

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Local runner"
  question: "The workflows run on a self-hosted local runner. Set one up for testing?"
  options:
    - label: "Yes, install runner inside the repo"
      description: "Installs to .github/runner/ — isolated per project, gitignored"
    - label: "Skip — use GitHub-hosted runners"
    - label: "Stop here"
```

If "No, I'll push my own code later": protect main immediately (smoke test skipped — no direct pushes needed):
```bash
gh api "repos/$REPO_PATH/branches/main/protection" -X PUT \
  --input - << 'EOF'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": false
  },
  "restrictions": null
}
EOF
```

If "Skip": mark step complete and move on.

If "Yes":

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll do**
```
Installs:   $REPO_NAME/.github/runner/  (gitignored)
Configures: runner bound to https://github.com/$REPO_PATH
Labels:     self-hosted, local
Patches:    runs-on → [self-hosted, local]
PAT:        1-day service-user PAT created + stored in Keychain → SNOWFLAKE_PAT secret
```

Call `exit_plan_mode`. Then execute directly:

```bash
mkdir -p "$REPO_NAME/.github/runner"
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz" \
  | tar xz -C "$REPO_NAME/.github/runner"
RUNNER_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/registration-token" -X POST -q .token)
"$REPO_NAME/.github/runner/config.sh" \
  --url "https://github.com/$REPO_PATH" \
  --token "$RUNNER_TOKEN" \
  --labels "self-hosted,local" \
  --unattended
sed -i '' 's/runs-on: ubuntu-latest/runs-on: [self-hosted, local]/g' \
  "$REPO_NAME/.github/workflows/cortex-scan.yml" \
  "$REPO_NAME/.github/workflows/cortex-fix.yml"
git -C "$REPO_NAME" add .github/workflows/
git -C "$REPO_NAME" commit -m "ci(workflows): use self-hosted local runner for testing [skip ci]"

# Start runner in background — safe across chat steps
nohup "$REPO_NAME/.github/runner/run.sh" \
  > "$REPO_NAME/.github/runner/runner.log" 2>&1 &
RUNNER_PID=$!
echo $RUNNER_PID > "$REPO_NAME/.github/runner/runner.pid"
sleep 3
grep -q "Listening for Jobs" "$REPO_NAME/.github/runner/runner.log" \
  && echo "✓ Runner is listening (PID $RUNNER_PID)" \
  || echo "Still starting — check: tail -f $REPO_NAME/.github/runner/runner.log"

python3 "$MANIFEST_OPS" fill-runner \
  --manifest "$MANIFEST" --pid "$RUNNER_PID" --runner-id ""

# Create 1-day PAT — token stored in Keychain, never shown
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
python3 "$PAT_OPS" create --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT" --manifest "$MANIFEST"
# Derive service name deterministically, pipe to secret (token never shown)
KEYCHAIN_SVC=$(python3 "$PAT_OPS" service-name --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT")
security find-generic-password -s "$KEYCHAIN_SVC" -a "$SF_USER" -w \
  | gh secret set SNOWFLAKE_PAT --repo "$REPO_PATH"
gh secret set SNOWFLAKE_USER --repo "$REPO_PATH" --body "$SF_USER"
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
If "Not yet": `tail -20 "$REPO_NAME/.github/runner/runner.log"` and re-ask.

**Post-step verification:**
```bash
gh api "repos/$REPO_PATH/actions/runners" --jq '.runners[] | {name, status}'
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```

### What we did
- Runner installed in `$REPO_NAME/.github/runner/` — runner PID `$RUNNER_PID` persisted in manifest
- Workflows patched to `runs-on: [self-hosted, local]`

---

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Configure done"
  question: "Setup complete. Want to test with a sample app?"
  options:
    - label: "Yes, run smoke test and watch the loop"
      description: "Copies a 3-issue Python app into demo/, enables Actions, commits and pushes"
    - label: "No, I'll push my own code later"
      description: "Skips smoke test — branch protection applied immediately"
    - label: "Stop here"
```
