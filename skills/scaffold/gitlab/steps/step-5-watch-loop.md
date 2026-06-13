# Step 5: Watch the Loop

> Part of the GitLab scaffold skill. Load when executing Step 5.
> Only execute if user chose "Yes, run smoke test" in Step 4.
> For SKILL_DIR resolution, see `references/manifest.md`.

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

**Enable pipelines first** (must happen before the runner can pick up jobs):
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```

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
Step 1: write smoke-test app (3 files) to $PROJECT_NAME/demo/
Step 2: commit + push  →  scan-code job triggers on the runner
Step 3: trigger pipeline + show URL
Step 4: revert when done  (git revert HEAD --no-edit && git push)
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

```bash
glab pipeline run --branch main
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
```

### What we did
- Pipelines enabled on `$PROJECT_PATH`
- Smoke-test app pushed to `demo/` — scan-code job triggered on the runner
- Issues and MRs will appear automatically

See `skills/scaffold/references/smoke-test.md` for expected output.

**Step 4 — Revert when done:**
```bash
cd "$PROJECT_NAME" && git revert HEAD --no-edit && git push
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
