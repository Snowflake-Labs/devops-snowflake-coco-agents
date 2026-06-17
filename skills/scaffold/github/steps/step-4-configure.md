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

**ICR: /scaffold = 48** — 1 instruction → 48 automated ops. See `docs/idd/icr.md`.

### Full setup path (`SETUP_MODE = "full"`)

Re-enable Actions and apply branch protection (same as quick start), then ask:

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

- If "Yes": load `github/steps/step-5-watch-loop.md`
- If "Skip": mark step complete, done

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_4
```

**ICR: /scaffold = 48** — 1 instruction → 48 automated ops. See `docs/idd/icr.md`.
