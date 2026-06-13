# Step 6: Clean Up

> Part of the GitHub scaffold skill. Load when executing Step 6.
> For teardown ordering rules, see `references/teardown.md`.

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
      description: "Keep repo and local clone; drop Snowflake objects and deregister runner"
    - label: "Keep everything"
```
If "Keep everything" → stop.

**Pre-flight: read manifest (see `references/teardown.md` for the full snippet)**
```bash
if [ -f "$MANIFEST" ]; then
  PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix)
  REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
  REPO_URL=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_url)
  RUNNER_PID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.pid)
  SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
  SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
  SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
fi
```

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Resources left running after a demo cost credits. Teardown runs in dependency
> order: disable CI first, then stop and deregister the runner, then drop
> Snowflake objects, then delete the remote repo, then remove the local clone.

**What we'll drop**
```
[tear down everything]
  1. Disable Actions
  2. Kill runner (PID: $RUNNER_PID)
  3. Deregister runner from GitHub API
  4. DROP USER      IF EXISTS $SF_USER
     DROP WAREHOUSE IF EXISTS $SF_WH
     DROP ROLE      IF EXISTS $SF_ROLE
  5. Delete remote: $REPO_URL
  6. Delete local:  ./$REPO_NAME/ (manifest included)

[Drop Snowflake only]
  1. Kill runner + deregister + restore ubuntu-latest + push
  2. Disable Actions
  3. Drop Snowflake (same 3 objects)
  4. Delete .coco-agent/ only (repo kept)
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
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'

if [ "${RUNNER_PID:-0}" -gt 0 ]; then kill "$RUNNER_PID" 2>/dev/null || true; sleep 2; fi
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
fi

snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"
gh repo delete "$REPO_PATH" --yes
rm -rf "$REPO_NAME"
rm -rf ".coco-agent/$REPO_NAME" 2>/dev/null; rmdir ".coco-agent" 2>/dev/null || true
echo "✓ $REPO_NAME removed — environment is clean"
```

**Execute — "Drop Snowflake only":**
```bash
if [ "${RUNNER_PID:-0}" -gt 0 ]; then kill "$RUNNER_PID" 2>/dev/null || true; sleep 2; fi
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
  sed -i '' 's/runs-on: \[self-hosted, local\]/runs-on: ubuntu-latest/g' \
    "$REPO_NAME/.github/workflows/cortex-scan.yml" \
    "$REPO_NAME/.github/workflows/cortex-fix.yml"
  git -C "$REPO_NAME" add .github/workflows/
  git -C "$REPO_NAME" commit -m "ci(workflows): restore ubuntu-latest runner [skip ci]"
  git -C "$REPO_NAME" push
fi

gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'
snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"
rm -rf "$REPO_NAME/.coco-agent/"
echo "✓ Snowflake resources dropped. Repo kept at $REPO_URL"
```

### What we did
- CI disabled, runner stopped and deregistered
- Snowflake objects dropped: `$SF_USER / $SF_WH / $SF_ROLE`
- [tear down everything] Repo deleted and local clone removed
- [Drop Snowflake only] Manifest removed — re-run scaffold to set up again

> ✓ **Done:** Environment is clean.
