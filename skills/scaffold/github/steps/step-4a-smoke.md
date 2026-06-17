# Step 5a: Smoke Test (GitHub)

> Sub-step of Step 5. Enables Actions then loads the shared generation flow.
> Set `REPO_OR_PROJECT_NAME="$REPO_NAME"` before loading the shared step.

**Enable Actions:**

```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": true}'
```

**Verify:** `gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled` → `true`.

```bash
REPO_OR_PROJECT_NAME="$REPO_NAME"
```

Load `shared/generate-demo.md`.

After the shared step pushes demo/, get the run ID and watch it live:

```bash
# Wait for Actions to register the push, then get the run ID
sleep 8
RUN_ID=$(gh run list --repo "$REPO_PATH" --workflow cortex-scan.yml \
  --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null)
echo "Actions run: $(gh repo view "$REPO_PATH" --json url -q .url)/actions/runs/$RUN_ID"

# Stream live — blocks until scan completes (~3-5 min). Ctrl-C to exit.
gh run watch "$RUN_ID" --repo "$REPO_PATH" --compact --exit-status || true

# Show results once run finishes
gh issue list --repo "$REPO_PATH" --label coco-agent
gh pr list   --repo "$REPO_PATH" --state open
```

When done, load `github/steps/step-5c-verify-smart-fix.md`.
