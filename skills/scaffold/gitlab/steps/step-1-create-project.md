# Step 1: Create Project

> Part of the GitLab scaffold skill. Load when executing Step 1.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

---

## Path A: Import existing project (`IMPORT_MODE = true`)

If user chose "Add to existing project" in the coordinator:

```bash
python3 "$MANIFEST_OPS" step-start \
  --manifest ".coco-agent/$PROJECT_NAME/manifest.toml" --step step_1

# Clone the existing project
glab repo clone "$PROJECT_PATH" "$PROJECT_NAME"

# Sparse copy CoCo CI + prompt files from template
git clone --filter=blob:none --sparse \
  https://gitlab.com/kameshsampath/gitlab-coco-agent \
  /tmp/coco-tpl-$$
git -C /tmp/coco-tpl-$$ sparse-checkout set .cortex/prompts

mkdir -p "$PROJECT_NAME/.cortex/prompts"
cp /tmp/coco-tpl-$$/.cortex/prompts/scan.md "$PROJECT_NAME/.cortex/prompts/"
cp /tmp/coco-tpl-$$/.cortex/prompts/fix.md  "$PROJECT_NAME/.cortex/prompts/"
# Merge .gitlab-ci.yml (append CoCo jobs if file already exists)
if [ -f "$PROJECT_NAME/.gitlab-ci.yml" ]; then
  echo "" >> "$PROJECT_NAME/.gitlab-ci.yml"
  tail -n +10 /tmp/coco-tpl-$$/.gitlab-ci.yml >> "$PROJECT_NAME/.gitlab-ci.yml"
  echo "⚠️ Merged CoCo jobs into existing .gitlab-ci.yml — review for conflicts"
else
  cp /tmp/coco-tpl-$$/.gitlab-ci.yml "$PROJECT_NAME/.gitlab-ci.yml"
fi
rm -rf /tmp/coco-tpl-$$

# Initialize manifest
PROJECT_URL="https://gitlab.com/$PROJECT_PATH"
python3 "$MANIFEST_OPS" init \
  --draft-path ".coco-agent/$PROJECT_NAME" \
  --prefix     "$PREFIX" \
  --repo-name  "$PROJECT_NAME" \
  --visibility "" \
  --run-mode   "$SKILL_MODE" \
  --platform   "gitlab" \
  --template-name "gitlab-coco-agent"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$PROJECT_NAME" \
  --to   "$PROJECT_NAME/.coco-agent" \
  --repo-path "$PROJECT_PATH" \
  --repo-url  "$PROJECT_URL" \
  --repo-name "$PROJECT_NAME"
git -C "$PROJECT_NAME" add .cortex/ .gitlab-ci.yml .coco-agent/
git -C "$PROJECT_NAME" commit -m "ci: add CoCo scan+fix pipeline and manifest [skip ci]"
git -C "$PROJECT_NAME" push
```

> ⚠️ Note: Pipelines are NOT disabled — the existing project may have active CI.
> Step-2 will offer to disable pipelines temporarily during Snowflake setup.
> Disabling affects ALL pipelines in the project, not just CoCo.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did (import path)
- Cloned `$PROJECT_PATH` into `./$PROJECT_NAME`
- Copied/merged `.gitlab-ci.yml`, `scan.md`, `fix.md` from template
- Manifest initialized and committed

---

## Path B: New project from template (`IMPORT_MODE = false`)


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

# Get namespace_id for the user/group
NAMESPACE_ID=$(glab api user | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Try to create blank project — rotate petname on collision (up to 3×)
for _i in 1 2 3; do
  CREATE_OUT=$(glab api "projects" --method POST \
    -F "name=$PROJECT_NAME" \
    -F "namespace_id=$NAMESPACE_ID" \
    -F "visibility=$PROJECT_VISIBILITY" \
    -F "initialize_with_readme=false" 2>&1)
  if echo "$CREATE_OUT" | python3 -c "
import sys, json
try:
    e = json.loads(sys.stdin.read())
    msg = str(e.get('message', {}))
    sys.exit(0 if 'Path has already been taken' in msg or 'has already been taken' in msg else 1)
except: sys.exit(1)
" 2>/dev/null; then
    PROJECT_NAME=$(python3 -c "
import random, string
print('-'.join(''.join(random.choices(string.ascii_lowercase, k=4)) for _ in range(2)))
")
    PROJECT_PATH="${GROUP}/${PROJECT_NAME}"
    ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")
    echo "Name taken — rotating to $PROJECT_NAME"
  else
    echo "✓ Project created: $PROJECT_PATH"
    break
  fi
done

# Clone template, rewire remote to new project, push main only
git clone https://gitlab.com/kameshsampath/gitlab-coco-agent "$PROJECT_NAME"
git -C "$PROJECT_NAME" remote set-url origin "https://gitlab.com/$PROJECT_PATH.git"
git -C "$PROJECT_NAME" push origin main

# Disable pipelines immediately — prevents spurious runs during setup
glab api "projects/$ENCODED_PATH" --method PUT -F "builds_access_level=disabled" 2>&1

# Move draft manifest into repo and fill project identity
PROJECT_URL="https://gitlab.com/$PROJECT_PATH"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$PROJECT_NAME" \
  --to   "$PROJECT_NAME/.coco-agent" \
  --repo-path "$PROJECT_PATH" \
  --repo-url  "$PROJECT_URL" \
  --repo-name "$PROJECT_NAME"
```

**Post-step verification:**
```bash
glab api "projects/$ENCODED_PATH" | python3 -c "import sys,json; print(json.load(sys.stdin)['visibility'])"
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
