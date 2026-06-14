# Step 4: Configure (Router)

> Part of the GitLab scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
SF_USER=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.user)
SF_ROLE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.role)
SF_WH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.warehouse)
```

**Gate check:**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_3 \
  || snow sql -q "DESC USER $SF_USER" --format json 2>&1
```
If empty or error: ⚠️ Complete Step 3 first.

Validate bot token: `glab api user | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])"` — if error, stop and fix token.

---

**Load `gitlab/steps/step-4a-variables.md`** — set CI/CD variables.

---

**Route by `$SETUP_MODE`:**

### Quick start path (`SETUP_MODE = "quick"`)

```bash
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

# Re-enable pipelines (was disabled in step 2)
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1

# Branch protection — check first (brownfield projects may already have rules)
EXISTING=$(glab api "projects/$ENCODED_PATH/protected_branches" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); \
    print(next((x['name'] for x in r if x['name']=='main'),''))" 2>/dev/null)
if [ -n "$EXISTING" ]; then
  echo "ℹ️  Existing branch protection on main — keeping current rules."
else
  glab api "projects/$ENCODED_PATH/protected_branches" \
    -X POST -F name=main -F push_access_level=0 -F merge_access_level=40
fi
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
echo "✓ Quick start complete. Push code to $PROJECT_PATH to trigger the scan+fix loop."
```

### Full setup path (`SETUP_MODE = "full"`)

Ask for local runner:
```
ask_user_question:
  header: "Local runner"
  question: "Set up a self-hosted local runner for testing?"
  options:
    - label: "Yes, install runner inside the project"
      description: "Installs to .gitlab/runner/ — isolated per project, gitignored"
    - label: "Skip — use GitLab.com shared runners"
    - label: "Stop here"
```
- If "Yes": load `gitlab/steps/step-4b-runner.md`
- If "Skip" or "Stop here": mark step complete, then ask about smoke test → Step 5 or stop

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```
