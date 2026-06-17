# Step 6: Clean Up (Router)

> Part of the GitHub scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).

```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

```
ask_user_question:
  header: "Clean Up"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources, delete GitHub repo, and remove local clone"
    - label: "Drop Snowflake only"
      description: "Keep repo and local clone; drop Snowflake objects only"
    - label: "Keep everything"
```

If "Keep everything" → stop.

**Pre-flight: read manifest**

```bash
if [ -f "$MANIFEST" ]; then
  REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
  REPO_URL=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_url)
  SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
  SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
  SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
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

Load `github/steps/step-6a-teardown.md`.
If `TEARDOWN_MODE=full`: also load `github/steps/step-6b-delete.md`.
If `TEARDOWN_MODE=snowflake-only`:

```bash
rm -rf "$REPO_NAME/.coco-agent/"
echo "✓ Snowflake resources dropped. Repo kept at $REPO_URL"
```
