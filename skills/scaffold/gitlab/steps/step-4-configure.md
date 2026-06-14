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

**Load in order:**

1. `gitlab/steps/step-4a-variables.md` — Set CI/CD variables

2. Ask for local runner:
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
   - If "Skip": mark step complete and move on

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```

Ask if user wants to run smoke test → route to Step 5 or stop.
