# Step 6: Clean Up (Router)

> Part of the GitLab scaffold skill.

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
      description: "Keep project and local clone; drop Snowflake objects only"
    - label: "Keep everything"
```

If "Keep everything" → stop.

**Pre-flight: read manifest**

```bash
if [ -f "$MANIFEST" ]; then
  PROJECT_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
  PROJECT_URL=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_url)
  SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
  SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
  SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
  ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")
fi
```

⚠️ MANDATORY: call `enter_plan_mode`. Present what will be dropped. Call `exit_plan_mode`.

Confirm (always fires — irreversible):

```
ask_user_question:
  header: "Confirm teardown"
  question: "⚠️ This is irreversible. Proceed with teardown?"
  options:
    - label: "Yes, tear down now"
    - label: "Abort"
```

Set `TEARDOWN_MODE` based on user choice:

- "tear down everything" → `TEARDOWN_MODE=full`
- "Drop Snowflake only" → `TEARDOWN_MODE=snowflake-only`

Load `gitlab/steps/step-6a-teardown.md`.
If `TEARDOWN_MODE=full`: also load `gitlab/steps/step-6b-delete.md`.
If `TEARDOWN_MODE=snowflake-only`:

```bash
rm -rf "$PROJECT_NAME/.coco-agent/"
echo "✓ Snowflake resources dropped. Project kept at $PROJECT_URL"
```
