# Step 5: Watch the Loop

> Part of the GitLab scaffold skill. Load when executing Step 5.
> Only execute if user chose "Yes, run smoke test" in Step 4.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

**Step 1 — Enable pipelines** (was disabled during setup — must happen before push kicks workflow):
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```
**Verify enabled:**
```bash
glab api "projects/$ENCODED_PATH" --jq .builds_access_level
```
Expected: `enabled`. If not, stop — pipelines must be enabled before pushing.

**Gate check — runner online (staleness-aware, 300s threshold):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_4 --threshold 300 \
  || glab api "projects/$ENCODED_PATH/runners" \
       --jq '[.[] | select(.description == "local-mac")] | length'
```
If 0:
> ⚠️ **Gate check failed:** No runner is online.
> Check: `tail -f $PROJECT_NAME/.gitlab/runner/runner.log`
> Restart: `nohup $PROJECT_NAME/.gitlab/runner/gitlab-runner run --config $PROJECT_NAME/.gitlab/runner/config.toml > $PROJECT_NAME/.gitlab/runner/runner.log 2>&1 &`

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> The smoke-test app contains 3 intentional security and correctness issues.
> Running it proves the loop end-to-end: scan finds issues, CoCo fixes them,
> MRs are opened automatically. No production code is touched.

**What we'll do**
```
Step 1: confirm pipelines enabled (already done above)
Step 2: write smoke-test app (3 files) to $PROJECT_NAME/demo/
Step 3: commit + push  →  scan-code job triggers on the runner
Step 4: confirm pipeline started — show pipelines URL
Step 5: revert + push when done  (git revert HEAD --no-edit && git push)
```

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_5
```

Read `skills/scaffold/references/smoke-test.md` and write the files from
`skills/scaffold/templates/smoke-test/` to `$PROJECT_NAME/demo/`.

```bash
cd "$PROJECT_NAME"
git add demo/
git commit -m "test(smoke): add intentional-issue app for CI/CD loop validation"
git push
```

**Confirm pipeline triggered** (mandatory — do not continue until push is confirmed):
```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
glab pipeline list --project "$PROJECT_PATH" 2>&1 | head -5
```

### What we did
- Pipelines enabled on `$PROJECT_PATH`
- Smoke-test app pushed to `demo/` — scan-code job triggered on the runner
- Issues and MRs will appear automatically

See `skills/scaffold/references/smoke-test.md` for expected output.

**Step 5 — Revert when done** (push is mandatory — triggers cleanup run):
```bash
cd "$PROJECT_NAME" && git revert HEAD --no-edit && git push
```

**Step 6 — Protect main branch** (smoke test complete — safe to restrict direct pushes):
```bash
glab api "projects/$ENCODED_PATH/protected_branches" \
  -X POST \
  -F name=main \
  -F push_access_level=0 \
  -F merge_access_level=40
```

**Step 7 — Revoke smoke test PAT** (if local runner was used):
```bash
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
python3 "$PAT_OPS" revoke --user "$SF_USER" && \
  glab variable delete SNOWFLAKE_PAT && \
  glab variable delete SNOWFLAKE_USER
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_5
```

---

⚠️ MANDATORY pause (repeatable until satisfied):
```
ask_user_question:
  header: "Watch the Loop"
  question: "Check for issues and MRs?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Stop here"
```

If "Check now":
```bash
echo "=== Issues ===" && glab issue list --label coco-agent
echo "=== MRs ===" && glab mr list --state opened
```
