# Step 1: Create Project

> Part of the GitHub scaffold skill. Load when executing Step 1.
> For SKILL_DIR resolution and manifest operations, see `references/manifest.md`.

```bash
# SKILL_DIR resolver — run once per step
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

**Pre-step guard — conflict detection:**
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
If "Use the existing repo": clone it, run `manifest_ops.py summary` if manifest exists, detect completed steps via API, present resume options.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Working from a versioned template guarantees every project starts from a
> known-good baseline — OIDC wiring, workflow structure, and prompt files are
> all pre-tested. You own the fork; the template repo is never modified.

**What we'll do**
```
Creates: $REPO_PATH  ($REPO_VISIBILITY, from github-coco-agent template)
Clones:  ./$REPO_NAME
```
Also show: `gh repo view https://github.com/Snowflake-Labs/github-coco-agent`

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$REPO_NAME/manifest.toml" --step step_1

gh repo create "$REPO_PATH" \
  --template https://github.com/Snowflake-Labs/github-coco-agent \
  --$REPO_VISIBILITY \
  --clone

# Disable Actions immediately — prevents spurious workflow runs during setup
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT --input - <<<'{"enabled": false}'

# Move draft manifest into repo and fill repo identity
REPO_URL=$(gh repo view "$REPO_PATH" --json url -q .url)
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$REPO_NAME" \
  --to   "$REPO_NAME/.coco-agent" \
  --repo-path "$REPO_PATH" \
  --repo-url  "$REPO_URL"
```

**Post-step verification:**
```bash
gh api "repos/$REPO_PATH" --jq .visibility
ls "$REPO_NAME"
```
If either fails:
> ⚠️ **Gate check failed:** Repo creation may not have completed fully.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did
- Repo created at `$REPO_URL` ($REPO_VISIBILITY)
- Local clone in `./$REPO_NAME`
- Manifest initialised at `$REPO_NAME/.coco-agent/manifest.toml`
