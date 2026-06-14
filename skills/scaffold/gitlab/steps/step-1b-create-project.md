# Step 1b: Create New GitLab Project from Template

> Sub-step of Step 1 — Path B (`IMPORT_MODE = false`).

Check for collision first:
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
If "Use the existing project": clone, run `manifest_ops.py summary`, detect completed steps, present resume options.

---

⚠️ MANDATORY: call `enter_plan_mode`. Present:
```
Creates: $PROJECT_PATH  ($PROJECT_VISIBILITY, from gitlab-coco-agent template)
Clones:  ./$PROJECT_NAME
```

Call `exit_plan_mode`. Then execute:

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$PROJECT_NAME/manifest.toml" --step step_1
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
NAMESPACE_ID=$(glab api user | _j "['id']")
for _i in 1 2 3; do
  CREATE_OUT=$(glab api "projects" --method POST \
    -F "name=$PROJECT_NAME" -F "namespace_id=$NAMESPACE_ID" \
    -F "visibility=$PROJECT_VISIBILITY" -F "initialize_with_readme=false" 2>&1)
  if echo "$CREATE_OUT" | python3 -c "
import sys,json
try:
  e=json.loads(sys.stdin.read())
  msg=str(e.get('message',{}))
  sys.exit(0 if 'Path has already been taken' in msg or 'has already been taken' in msg else 1)
except: sys.exit(1)
" 2>/dev/null; then
    PROJECT_NAME=$(python3 -c "import random,string; print('-'.join(''.join(random.choices(string.ascii_lowercase,k=4)) for _ in range(2)))")
    PROJECT_PATH="${GROUP}/${PROJECT_NAME}"
    ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH',safe=''))")
    echo "Name taken — rotating to $PROJECT_NAME"
  else
    echo "✓ Project created: $PROJECT_PATH"; break
  fi
done
git clone https://gitlab.com/kameshsampath/gitlab-coco-agent "$PROJECT_NAME"
git -C "$PROJECT_NAME" remote set-url origin "https://gitlab.com/$PROJECT_PATH.git"
git -C "$PROJECT_NAME" push origin main
# Disable pipelines immediately
glab api "projects/$ENCODED_PATH" --method PUT -F "builds_access_level=disabled" 2>&1
PROJECT_URL="https://gitlab.com/$PROJECT_PATH"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$PROJECT_NAME" --to "$PROJECT_NAME/.coco-agent" \
  --repo-path "$PROJECT_PATH" --repo-url "$PROJECT_URL" --repo-name "$PROJECT_NAME"
```

**Verify:** `glab api "projects/$ENCODED_PATH" | _j "['visibility']"` and `ls "$PROJECT_NAME"`.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did
- Project created at `$PROJECT_URL` ($PROJECT_VISIBILITY) from template
- Pipelines disabled — re-enabled in Step 5 just before smoke test
- Manifest initialized at `$PROJECT_NAME/.coco-agent/manifest.toml`
