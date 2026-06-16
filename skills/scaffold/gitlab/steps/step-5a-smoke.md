# Step 5a: Smoke Test (GitLab)

> Sub-step of Step 5. Enables pipelines and pushes the smoke-test app.

```bash
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

**Enable pipelines** (was disabled during setup — must happen before push):

```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```

**Verify:** `glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"` → expected `enabled`.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll do**

```
Step 1: confirm pipelines enabled (already done above)
Step 2: write smoke-test app (3 files) to $PROJECT_NAME/demo/
Step 3: commit + push  →  scan-code job triggers on GitLab shared runner
Step 4: confirm pipeline started — show pipelines URL
```

Call `exit_plan_mode`. Then execute:

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

**Confirm pipeline triggered** (mandatory — do not continue until push confirmed):

```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
glab pipeline list --project "$PROJECT_PATH" 2>&1 | head -5
```

### What we did

- Pipelines enabled on `$PROJECT_PATH`
- Smoke-test app pushed to `demo/` — scan-code job triggered on the runner

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
