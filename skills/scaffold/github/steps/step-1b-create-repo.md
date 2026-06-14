# Step 1b: Create New GitHub Repo from Template

> Sub-step of Step 1 — Path B (`IMPORT_MODE = false`).

Check for collision first:
```bash
gh api "repos/$REPO_PATH" 2>&1
```
If EXISTS and `USING_GENERATED = true`: rotate petname (up to 3×), re-present name question.
If EXISTS and `USING_GENERATED = false`:
```
ask_user_question:
  header: "Repo exists"
  question: "`$REPO_PATH` already exists. What would you like to do?"
  options:
    - label: "Use the existing repo"
    - label: "Choose a different name"
    - label: "Abort"
```
If "Use the existing repo": clone it, run `manifest_ops.py summary` if manifest exists, detect completed steps, present resume options.

---

⚠️ MANDATORY: call `enter_plan_mode`. Present:
```
Creates: $REPO_PATH  ($REPO_VISIBILITY, from github-coco-agent template)
Clones:  ./$REPO_NAME
```
Also show: `gh repo view https://github.com/Snowflake-Labs/github-coco-agent`

Call `exit_plan_mode`. Then execute:

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$REPO_NAME/manifest.toml" --step step_1
gh repo create "$REPO_PATH" \
  --template https://github.com/Snowflake-Labs/github-coco-agent \
  --$REPO_VISIBILITY --clone
# Disable Actions immediately — prevents spurious workflow runs during setup
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'
REPO_URL=$(gh repo view "$REPO_PATH" --json url -q .url)
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$REPO_NAME" --to "$REPO_NAME/.coco-agent" \
  --repo-path "$REPO_PATH" --repo-url "$REPO_URL"
```

**Verify:** `gh api "repos/$REPO_PATH" --jq .visibility` and `ls "$REPO_NAME"`.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did
- Repo created at `$REPO_URL` ($REPO_VISIBILITY) from template
- Actions disabled — re-enabled in Step 5 just before smoke test
- Manifest initialized at `$REPO_NAME/.coco-agent/manifest.toml`
