# Step 4: Configure (Router)

> Part of the GitHub scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
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

---

**Load `github/steps/step-4a-secrets.md`** — set GH secrets + workflow permissions.

---

**Route by `$SETUP_MODE`:**

### Quick start path (`SETUP_MODE = "quick"`)

```bash
# Re-enable Actions (was disabled in step 2)
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": true}'

# Branch protection — check first (brownfield repos may already have rules)
EXISTING=$(gh api "repos/$REPO_PATH/branches/main/protection" 2>/dev/null)
if [ -n "$EXISTING" ]; then
  echo "ℹ️  Existing branch protection found on main — keeping current rules."
else
  gh api "repos/$REPO_PATH/branches/main/protection" -X PUT \
    --input - << 'EOF'
{"required_status_checks":null,"enforce_admins":false,
 "required_pull_request_reviews":{"required_approving_review_count":1},
 "restrictions":null}
EOF
fi
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
echo "✓ Quick start complete. Push code to $REPO_PATH to trigger the scan+fix loop."
```

### Full setup path (`SETUP_MODE = "full"`)

Ask for local runner:
```
ask_user_question:
  header: "Local runner"
  question: "Set up a self-hosted local runner for testing?"
  options:
    - label: "Yes, install runner inside the repo"
    - label: "Skip — use GitHub-hosted runners"
    - label: "Stop here"
```
- If "Yes": load `github/steps/step-4b-runner.md`
- If "Skip" or "Stop here": mark step complete, then ask about smoke test → Step 5 or stop

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```
