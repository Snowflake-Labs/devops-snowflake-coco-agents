# Step 6: Clean Up

> Part of the GitLab scaffold skill. Load when executing Step 6.
> For teardown ordering rules, see `references/teardown.md`.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

```
ask_user_question:
  header: "Clean Up"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources, delete GitLab project, and remove local clone"
    - label: "Drop Snowflake only"
      description: "Keep project and local clone; drop Snowflake objects and deregister runner"
    - label: "Keep everything"
```
If "Keep everything" → stop.

**Pre-flight: read manifest (see `references/teardown.md` for the full snippet)**
```bash
if [ -f "$MANIFEST" ]; then
  PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix)
  PROJECT_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
  PROJECT_URL=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_url)
  RUNNER_PID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.pid)
  RUNNER_ID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.runner_id)
  SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
  SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
  SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
  ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")
fi
```

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Resources left running cost credits. Teardown: disable CI first so no new
> jobs fire, stop and deregister runner, drop Snowflake objects, delete the
> remote project, then remove the local clone.

**What we'll drop**
```
[tear down everything]
  1. Disable pipelines
  2. Kill runner (PID: $RUNNER_PID)
  3. Deregister runner (ID: $RUNNER_ID)
  4. DROP USER      IF EXISTS $SF_USER
     DROP WAREHOUSE IF EXISTS $SF_WH
     DROP ROLE      IF EXISTS $SF_ROLE
  5. Delete remote: $PROJECT_URL
  6. Delete local:  ./$PROJECT_NAME/ (manifest included)

[Drop Snowflake only]
  1. Kill runner + deregister + remove tags: [local] + push
  2. Disable pipelines
  3. Drop Snowflake (same 3 objects)
  4. Delete .coco-agent/ only (project kept)
```

Call `exit_plan_mode`. Then ask (always fires — destructive and irreversible):
```
ask_user_question:
  header: "Confirm teardown"
  question: "⚠️ This is irreversible. Proceed with teardown?"
  options:
    - label: "Yes, tear down now"
    - label: "Abort"
```

**Execute — "tear down everything":**
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1

if [ "${RUNNER_PID:-0}" -gt 0 ]; then kill "$RUNNER_PID" 2>/dev/null || true; sleep 2; fi
if [ -n "$RUNNER_ID" ] && [ "$RUNNER_ID" != "0" ]; then
  glab api "projects/$ENCODED_PATH/runners/$RUNNER_ID" -X DELETE
fi

snow sql -f "$PROJECT_NAME/snowflake/teardown.sql" \
  -D "PREFIX=$PREFIX" --enable-templating STANDARD
glab project delete "$PROJECT_PATH" --yes
rm -rf "$PROJECT_NAME"
rm -rf ".coco-agent/$PROJECT_NAME" 2>/dev/null; rmdir ".coco-agent" 2>/dev/null || true
echo "✓ $PROJECT_NAME removed — environment is clean"
```

**Execute — "Drop Snowflake only":**
```bash
if [ "${RUNNER_PID:-0}" -gt 0 ]; then kill "$RUNNER_PID" 2>/dev/null || true; sleep 2; fi
if [ -n "$RUNNER_ID" ] && [ "$RUNNER_ID" != "0" ]; then
  glab api "projects/$ENCODED_PATH/runners/$RUNNER_ID" -X DELETE
  python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)\n  tags: \[local\]", rf"\1", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Reverted: tags: [local] removed")
PYEOF
  git -C "$PROJECT_NAME" add .gitlab-ci.yml
  git -C "$PROJECT_NAME" commit -m "ci: restore default runner [skip ci]"
  git -C "$PROJECT_NAME" push
fi

glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
snow sql -f "$PROJECT_NAME/snowflake/teardown.sql" \
  -D "PREFIX=$PREFIX" --enable-templating STANDARD
rm -rf "$PROJECT_NAME/.coco-agent/"
echo "✓ Snowflake resources dropped. Project kept at $PROJECT_URL"
```

### What we did
- CI disabled, runner stopped and deregistered
- Snowflake objects dropped: `$SF_USER / $SF_WH / $SF_ROLE`
- [tear down everything] Project deleted and local clone removed
- [Drop Snowflake only] Manifest removed — re-run scaffold to set up again

> ✓ **Done:** Environment is clean.
