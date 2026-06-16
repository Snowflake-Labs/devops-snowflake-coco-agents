# Step 5a-generate: Generate Demo App (GitLab)

> Loaded from step-5a-smoke.md after the user confirms the generation prompt.
> `$APP_TYPE`, `$USE_CASE_DESC`, and the prompt string are set in step-5a.

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_5
```

Write the prompt string to `/tmp/generate-demo-$$.md` using your **Write tool**.

Then run:

```bash
cd "$PROJECT_NAME"
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

**Confirm pipeline triggered:**

```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
glab pipeline list --project "$PROJECT_PATH" 2>&1 | head -5
```

### What we did

- CoCo generated `$APP_TYPE` demo app in `demo/`
- Scan-code job triggered on `$PROJECT_PATH`

⚠️ MANDATORY pause (repeatable):

```
ask_user_question:
  header: "Watch the Loop"
  question: "Check for issues and MRs on $PROJECT_PATH?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Done — continue to revert"
```

If "Check now": `glab issue list --label coco-agent` and `glab mr list --state opened`

When done, load `gitlab/steps/step-5c-verify-smart-fix.md`.
