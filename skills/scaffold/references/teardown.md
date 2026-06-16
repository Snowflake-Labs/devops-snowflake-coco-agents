# Teardown Reference

Shared teardown ordering rules for both GitHub and GitLab scaffold skills.
Referenced by `step-6-clean-up.md` in both platform step directories.

---

## Mandatory Teardown Order

Always execute in this dependency order — skipping a step leaves orphaned objects.

### "Tear down everything"

```
1. Disable CI           ← no new jobs fire during teardown
2. Drop Snowflake       ← USER, WAREHOUSE, ROLE (reverse dependency order)
3. Delete remote repo   ← project/repo deleted from GitHub or GitLab
4. Delete local clone   ← rm -rf $REPO_NAME (manifest inside — gone with it)
   + clean draft dir    ← rm -rf .coco-agent/$REPO_NAME if draft exists
```

### "Drop Snowflake only"

```
1. Disable CI           ← no live runner, keep pipelines off
2. Drop Snowflake       ← USER, WAREHOUSE, ROLE
3. Delete .coco-agent/  ← manifest removed (repo and clone kept)
```

---

## Pre-flight: Read Manifest

Always load teardown variables from the manifest before entering plan mode.
For SKILL_DIR resolution, see `references/manifest.md`.

```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
if [ -f "$MANIFEST" ]; then
  PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix)
  REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
  REPO_URL=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_url)
  SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
  SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
  SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
  echo "✓ Manifest loaded: PREFIX=$PREFIX REPO_PATH=$REPO_PATH"
else
  echo "No manifest — enter PREFIX and REPO_PATH manually"
  # ask_user_question for PREFIX and REPO_PATH
fi
```

---

## Snowflake DROP Statements

**SQL guard — validate names before dropping.** Object names are read from the
manifest and must match the `*_COCO_AGENT_{USER|ROLE|WH}` pattern. This prevents
accidentally dropping objects that weren't created by this scaffold.

```bash
# Guard: abort if any name doesn't match the COCO_AGENT pattern
for _obj in "$SF_USER" "$SF_WH" "$SF_ROLE"; do
  if [[ ! "$_obj" =~ _COCO_AGENT_(USER|ROLE|WH)$ ]]; then
    echo "⚠️  Guard blocked: '$_obj' does not match COCO_AGENT naming — aborting Snowflake drop"
    exit 1
  fi
done
```

Show these verbatim in the "What we'll drop" plan preview:

```sql
DROP USER      IF EXISTS $SF_USER;
DROP WAREHOUSE IF EXISTS $SF_WH;
DROP ROLE      IF EXISTS $SF_ROLE;
```

Execute using the `snowflake_sql_execute` tool (inline — no file dependency):

```sql
DROP USER      IF EXISTS $SF_USER;
DROP WAREHOUSE IF EXISTS $SF_WH;
DROP ROLE      IF EXISTS $SF_ROLE;
```

---

## Post-teardown Manifest Cleanup

- **"Tear down everything"**: manifest is deleted with `rm -rf $REPO_NAME`.
  Also clean draft: `rm -rf ".coco-agent/$REPO_NAME" 2>/dev/null; rmdir ".coco-agent" 2>/dev/null || true`
- **"Drop Snowflake only"**: explicitly delete manifest: `rm -rf "$REPO_NAME/.coco-agent/"`
