# Step 5a-generate: Generate Demo App (GitHub)

> Loaded from step-5a-smoke.md after the user confirms the generation prompt.
> `$APP_TYPE`, `$USE_CASE_DESC`, and the prompt string are set in step-5a.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_5
```

Write the prompt string to `/tmp/generate-demo-$$.md` using your **Write tool**.

Then run:

```bash
cd "$REPO_NAME"
cortex exec --file /tmp/generate-demo-$$.md \
  -c "$SNOWFLAKE_CONN" --bypass --no-history \
  --allowed "Write" --allowed "Bash(mkdir *)"
```

Commit and push the generated files:

```bash
git add demo/
git commit -m "test(smoke): generate $APP_TYPE demo app for CI/CD loop validation"
git push
```

**Confirm workflow triggered:**

```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
gh run list --repo "$REPO_PATH" --limit 3
```

### What we did

- CoCo generated `$APP_TYPE` demo app in `demo/`
- Scan workflow triggered on `$REPO_PATH`

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
