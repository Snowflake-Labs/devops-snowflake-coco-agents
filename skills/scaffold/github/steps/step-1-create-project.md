# Step 1: Create Project

> Part of the GitHub scaffold skill. Load when executing Step 1.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

---

## Path A: Import existing repo (`IMPORT_MODE = true`)

If user chose "Add to existing repo" in the coordinator:

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$REPO_NAME/manifest.toml" --step step_1

# Clone the existing repo
gh repo clone "$REPO_PATH" "$REPO_NAME"

# Sparse copy CoCo workflow + prompt files from template
git clone --filter=blob:none --sparse \
  https://github.com/Snowflake-Labs/github-coco-agent \
  /tmp/coco-tpl-$$
git -C /tmp/coco-tpl-$$ sparse-checkout set .github/workflows .cortex/prompts

mkdir -p "$REPO_NAME/.github/workflows" "$REPO_NAME/.cortex/prompts"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-scan.yml "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-fix.yml  "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.cortex/prompts/scan.md "$REPO_NAME/.cortex/prompts/"
cp /tmp/coco-tpl-$$/.cortex/prompts/fix.md  "$REPO_NAME/.cortex/prompts/"
rm -rf /tmp/coco-tpl-$$

# Initialize manifest
REPO_URL=$(gh repo view "$REPO_PATH" --json url -q .url)
python3 "$MANIFEST_OPS" init \
  --draft-path ".coco-agent/$REPO_NAME" \
  --prefix     "$PREFIX" \
  --repo-name  "$REPO_NAME" \
  --visibility "" \
  --run-mode   "$SKILL_MODE" \
  --platform   "github" \
  --template-name "github-coco-agent"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$REPO_NAME" \
  --to   "$REPO_NAME/.coco-agent" \
  --repo-path "$REPO_PATH" \
  --repo-url  "$REPO_URL"

# Commit CoCo files to existing repo
git -C "$REPO_NAME" add .github/workflows/cortex-scan.yml \
  .github/workflows/cortex-fix.yml .cortex/ .coco-agent/
git -C "$REPO_NAME" commit -m "ci: add CoCo scan+fix workflow and manifest [skip ci]"
git -C "$REPO_NAME" push
```

> ⚠️ Note: Actions are NOT disabled — the existing repo may have active CI.
> Step-2 will offer to disable Actions temporarily during Snowflake setup.
> Disabling affects ALL workflows in the repo, not just CoCo.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did (import path)
- Cloned `$REPO_PATH` into `./$REPO_NAME`
- Copied `cortex-scan.yml`, `cortex-fix.yml`, `scan.md`, `fix.md` from template
- Manifest initialized and committed

---

## Path B: New repo from template (`IMPORT_MODE = false`)
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
