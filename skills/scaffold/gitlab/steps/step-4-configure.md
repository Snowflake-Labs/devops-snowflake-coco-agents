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

**ICR: /scaffold = 48** — 1 instruction → 48 automated ops. See `docs/idd/icr.md`.

### Full setup path (`SETUP_MODE = "full"`)

Re-enable pipelines and apply branch protection (same as quick start), then ask:

```
ask_user_question:
  header: "Smoke test"
  question: "Run the smoke test now to validate the pipeline end-to-end?"
  options:
    - label: "Yes — run smoke test"
      description: "Pushes a sample app to demo/, watches the scan→issue→fix loop"
    - label: "Skip — done"
      description: "Pipeline is live, trigger a scan manually when ready"
```

- If "Yes": load `gitlab/steps/step-5-watch-loop.md`
- If "Skip": mark step complete, done

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```

**ICR: /scaffold = 48** — 1 instruction → 48 automated ops. See `docs/idd/icr.md`.
