# Step 1: Create Project

> Part of the GitLab scaffold skill. Load when executing Step 1.
> For SKILL_DIR resolution and manifest operations, see `references/manifest.md`.

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

**Pre-step guard — conflict detection:**
```bash
glab api "projects/$ENCODED_PATH" 2>&1
```
If EXISTS and `USING_GENERATED = true`: rotate petname (up to 3×), re-present name question.
If EXISTS and `USING_GENERATED = false`:
```
ask_user_question:
  header: "Project exists"
  question: "`$PROJECT_PATH` already exists. What would you like to do?"
  options:
    - label: "Use the existing project"
    - label: "Choose a different name"
    - label: "Abort"
```
If "Use the existing project": clone it, run `manifest_ops.py summary` if manifest exists, detect completed steps via API, present resume options.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Working from a versioned template guarantees every project starts from a
> known-good baseline — OIDC wiring, pipeline structure, and prompt files are
> all pre-tested. You own the fork; the template project is never modified.

**What we'll do**
```
Creates: $PROJECT_PATH  ($PROJECT_VISIBILITY, from gitlab-coco-agent template)
Clones:  ./$PROJECT_NAME
```

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start \
  --manifest ".coco-agent/$PROJECT_NAME/manifest.toml" --step step_1

glab project create "$PROJECT_NAME" \
  --group "$GROUP" \
  --template-project https://gitlab.com/kameshsampath/gitlab-coco-agent \
  --$PROJECT_VISIBILITY

glab repo clone "$PROJECT_PATH"

# Disable pipelines immediately — prevents spurious runs during setup
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1

# Move draft manifest into repo and fill project identity
PROJECT_URL="https://gitlab.com/$PROJECT_PATH"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$PROJECT_NAME" \
  --to   "$PROJECT_NAME/.coco-agent" \
  --repo-path "$PROJECT_PATH" \
  --repo-url  "$PROJECT_URL"
```

**Post-step verification:**
```bash
glab api "projects/$ENCODED_PATH" --jq .visibility
ls "$PROJECT_NAME"
```
If either fails:
> ⚠️ **Gate check failed:** Project creation may not have completed fully.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did
- Project created at `$PROJECT_URL` ($PROJECT_VISIBILITY)
- Local clone in `./$PROJECT_NAME`
- Manifest initialised at `$PROJECT_NAME/.coco-agent/manifest.toml`
