# Step 5: Watch the Loop

> Part of the GitHub scaffold skill. Load when executing Step 5.
> Only execute if user chose "Yes, run smoke test" in Step 4.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

**Step 1 — Enable Actions** (was disabled during setup — must happen before push kicks workflow):
```bash
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT --input - <<<'{"enabled": true}'
```
**Verify enabled:**
```bash
gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```
Expected: `true`. If not, stop — Actions must be enabled before pushing.

**Gate check — runner online (staleness-aware, 300s threshold):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_4 --threshold 300 \
  || gh api "repos/$REPO_PATH/actions/runners" --jq '.runners | length'
```
If 0:
> ⚠️ **Gate check failed:** No runner is online.
> Check: `tail -f $REPO_NAME/.github/runner/runner.log`
> Restart: `nohup $REPO_NAME/.github/runner/run.sh > $REPO_NAME/.github/runner/runner.log 2>&1 & echo $! > $REPO_NAME/.github/runner/runner.pid`

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> The smoke-test app contains 3 intentional security and correctness issues.
> Running it proves the loop end-to-end: scan finds issues, fix agents patch
> them, PRs are opened automatically. No production code is touched.

**What we'll do**
```
Step 1: confirm Actions enabled (already done above)
Step 2: write smoke-test app (3 files) to $REPO_NAME/demo/
Step 3: commit + push  →  scan workflow triggers on the runner
Step 4: confirm workflow started — show Actions URL
Step 5: revert + push when done  (git revert HEAD --no-edit && git push)
```

Call `exit_plan_mode`. Then execute directly:

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

**Confirm workflow triggered** (mandatory — do not continue until push is confirmed):
```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
gh run list --repo "$REPO_PATH" --limit 3
```

### What we did
- Actions enabled on `$REPO_PATH`
- Smoke-test app pushed to `demo/` — scan workflow triggered on the runner
- Issues and PRs will appear automatically

See `skills/scaffold/references/smoke-test.md` for expected output.

**Step 5 — Revert when done** (push is mandatory — triggers cleanup run):
```bash
cd "$REPO_NAME" && git revert HEAD --no-edit && git push
```

**Step 6 — Protect main branch** (smoke test complete — safe to restrict direct pushes):
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

**Step 7 — Revoke smoke test PAT** (if local runner was used):
```bash
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
PAT_NAME=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.pat_name 2>/dev/null || echo "")
if [ -n "$PAT_NAME" ]; then
  python3 "$PAT_OPS" revoke --user "$SF_USER" --manifest "$MANIFEST"
  gh secret delete SNOWFLAKE_PAT --repo "$REPO_PATH"
  gh secret delete SNOWFLAKE_USER --repo "$REPO_PATH"
else
  echo "No PAT in manifest — skipping PAT revocation"
fi
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_5
```

---

⚠️ MANDATORY pause (repeatable until satisfied):
```
ask_user_question:
  header: "Watch the Loop"
  question: "Check for issues and PRs?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Stop here"
```

If "Check now":
```bash
echo "=== Issues ===" && gh issue list --repo "$REPO_PATH" --label coco-agent
echo "=== PRs ===" && gh pr list --repo "$REPO_PATH" --state open
```
