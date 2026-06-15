# Step 5a: Smoke Test (GitHub)

> Sub-step of Step 5. Enables Actions and pushes the smoke-test app.

**Enable Actions** (was disabled during setup — must happen before push):
```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": true}'
```
**Verify:** `gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled` → expected `true`.

**Gate check — runner online (staleness-aware, 300s threshold):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_4 --threshold 300 \
  || gh api "repos/$REPO_PATH/actions/runners" --jq '.runners | length'
```
If 0: ⚠️ No runner online. Check: `tail -f $REPO_NAME/.github/runner/runner.log`

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll do**
```
Step 1: confirm Actions enabled (already done above)
Step 2: write smoke-test app (3 files) to $REPO_NAME/demo/
Step 3: commit + push  →  scan workflow triggers on the runner
Step 4: confirm workflow started — show Actions URL
```

Call `exit_plan_mode`. Then execute:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_5
```

Read `skills/scaffold/references/smoke-test.md` and write the files from
`skills/scaffold/templates/smoke-test/` to `$REPO_NAME/demo/`.

```bash
cd "$REPO_NAME"
git add demo/
git commit -m "test(smoke): add intentional-issue app for CI/CD loop validation"
git push
```

**Confirm workflow triggered** (mandatory — do not continue until push confirmed):
```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
gh run list --repo "$REPO_PATH" --limit 3
```

### What we did
- Actions enabled on `$REPO_PATH`
- Smoke-test app pushed to `demo/` — scan workflow triggered on the runner

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
