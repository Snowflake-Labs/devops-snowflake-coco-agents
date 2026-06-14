# Teardown Reference

Shared teardown ordering rules for both GitHub and GitLab scaffold skills.
Referenced by `step-6-clean-up.md` in both platform step directories.

---

## Mandatory Teardown Order

Always execute in this dependency order — skipping a step leaves orphaned objects.

### "Tear down everything"

```
1. Disable CI           ← no new jobs fire during teardown
2. Kill runner PID      ← graceful stop before deregistration
3. Deregister runner    ← release the runner slot from the API
4. Drop Snowflake       ← USER, WAREHOUSE, ROLE (reverse dependency order)
5. Delete remote repo   ← project/repo deleted from GitHub or GitLab
6. Delete local clone   ← rm -rf $REPO_NAME (manifest inside — gone with it)
   + clean draft dir    ← rm -rf .coco-agent/$REPO_NAME if draft exists
```

No workflow patch commit in this path — the repo is being deleted anyway.

### "Drop Snowflake only"

```
1. Kill runner PID      ← graceful stop
2. Deregister runner    ← release API slot
3. Patch workflows      ← restore ubuntu-latest / remove tags: [local]
4. Commit + push        ← repo must be left in consistent state
5. Disable CI           ← no live runner, keep pipelines off
6. Drop Snowflake       ← USER, WAREHOUSE, ROLE
7. Delete .coco-agent/  ← manifest removed (repo and clone kept)
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
  RUNNER_PID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.pid)
  RUNNER_ID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.runner_id)
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

If `snowflake.pat_name` is set in the manifest, also revoke the PAT first:
```sql
ALTER USER $SF_USER DROP PROGRAMMATIC ACCESS TOKEN $PAT_NAME;
```

---

## Kill + Deregister Runner

**GitHub:**
```bash
# Kill
if [ "${RUNNER_PID:-0}" -gt 0 ]; then
  kill "$RUNNER_PID" 2>/dev/null || true; sleep 2
fi
# Deregister (no workflow patch when deleting repo)
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" \
    -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
fi
```

**GitLab:**
```bash
# Kill
if [ "${RUNNER_PID:-0}" -gt 0 ]; then
  kill "$RUNNER_PID" 2>/dev/null || true; sleep 2
fi
# Deregister via API (runner_id from manifest)
if [ -n "$RUNNER_ID" ] && [ "$RUNNER_ID" != "0" ]; then
  glab api "projects/$ENCODED_PATH/runners/$RUNNER_ID" -X DELETE
fi
```

---

## Post-teardown Manifest Cleanup

- **"Tear down everything"**: manifest is deleted with `rm -rf $REPO_NAME`.
  Also clean draft: `rm -rf ".coco-agent/$REPO_NAME" 2>/dev/null; rmdir ".coco-agent" 2>/dev/null || true`
- **"Drop Snowflake only"**: explicitly delete manifest: `rm -rf "$REPO_NAME/.coco-agent/"`
