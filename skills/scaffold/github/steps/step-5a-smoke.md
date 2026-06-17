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

After the shared step pushes demo/, verify CI triggered and watch the loop:

```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
gh run list --repo "$REPO_PATH" --limit 3
```

⚠️ MANDATORY pause (repeatable):

```
ask_user_question:
  header: "Watch the Loop"
  question: "Check for issues and PRs on $REPO_PATH?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Done — continue to revert"
```

If "Check now": `gh issue list --repo "$REPO_PATH" --label coco-agent` and `gh pr list --repo "$REPO_PATH" --state open`

When done, load `github/steps/step-5c-verify-smart-fix.md`.
