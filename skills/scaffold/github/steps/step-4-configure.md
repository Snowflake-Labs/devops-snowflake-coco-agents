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

**Load in order:**

1. `github/steps/step-4a-secrets.md` — Set GH secrets + workflow permissions

2. Ask for local runner:
   ```
   ask_user_question:
     header: "Local runner"
     question: "Set up a self-hosted local runner for testing?"
     options:
       - label: "Yes, install runner inside the repo"
       - label: "Skip — use GitHub-hosted runners"
       - label: "No, I'll push my own code later"
         description: "Skips smoke test — branch protection applied immediately"
       - label: "Stop here"
   ```
   - If "Yes": load `github/steps/step-4b-runner.md`
   - If "No, I'll push my own code later": apply branch protection now (see below), then mark complete
   - If "Skip": mark step complete and move on

**Branch protection (if skipping smoke test):**
```bash
gh api "repos/$REPO_PATH/branches/main/protection" -X PUT \
  --input - << 'EOF'
{"required_status_checks":null,"enforce_admins":false,
 "required_pull_request_reviews":{"required_approving_review_count":1},
 "restrictions":null}
EOF
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```

Ask if user wants to run smoke test → route to Step 5 or stop.
