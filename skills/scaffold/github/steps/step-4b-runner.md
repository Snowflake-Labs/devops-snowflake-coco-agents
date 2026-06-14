# Step 4b: GitHub Local Runner Setup (Optional)

> Sub-step of Step 4. Load only if user chose "Yes, install runner".

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll do**
```
Installs:   $REPO_NAME/.github/runner/  (gitignored)
Configures: runner bound to https://github.com/$REPO_PATH
Labels:     self-hosted, local
Patches:    runs-on → [self-hosted, local]
PAT:        1-day service-user PAT — Keychain → SNOWFLAKE_PAT secret
```

Call `exit_plan_mode`. Then execute:

```bash
mkdir -p "$REPO_NAME/.github/runner"
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz" \
  | tar xz -C "$REPO_NAME/.github/runner"
RUNNER_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/registration-token" -X POST -q .token)
"$REPO_NAME/.github/runner/config.sh" \
  --url "https://github.com/$REPO_PATH" --token "$RUNNER_TOKEN" \
  --labels "self-hosted,local" --unattended
sed -i '' 's/runs-on: ubuntu-latest/runs-on: [self-hosted, local]/g' \
  "$REPO_NAME/.github/workflows/cortex-scan.yml" \
  "$REPO_NAME/.github/workflows/cortex-fix.yml"
git -C "$REPO_NAME" add .github/workflows/
git -C "$REPO_NAME" commit -m "ci(workflows): use self-hosted local runner for testing [skip ci]"
nohup "$REPO_NAME/.github/runner/run.sh" > "$REPO_NAME/.github/runner/runner.log" 2>&1 &
RUNNER_PID=$!
echo $RUNNER_PID > "$REPO_NAME/.github/runner/runner.pid"
sleep 3
grep -q "Listening for Jobs" "$REPO_NAME/.github/runner/runner.log" \
  && echo "✓ Runner is listening (PID $RUNNER_PID)" \
  || echo "Still starting — check: tail -f $REPO_NAME/.github/runner/runner.log"
python3 "$MANIFEST_OPS" fill-runner --manifest "$MANIFEST" --pid "$RUNNER_PID" --runner-id ""
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
python3 "$PAT_OPS" create --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT" --manifest "$MANIFEST"
KSVC=$(python3 "$PAT_OPS" service-name --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT")
security find-generic-password -s "$KSVC" -a "$SF_USER" -w | gh secret set SNOWFLAKE_PAT --repo "$REPO_PATH"
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
