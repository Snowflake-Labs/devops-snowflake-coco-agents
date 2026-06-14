# Step 5b: Revert, Protect, Revoke (GitHub)

> Sub-step of Step 5. Load after smoke test is confirmed done.

**Revert smoke-test commit** (push triggers cleanup run):
```bash
cd "$REPO_NAME" && git revert HEAD --no-edit && git push
```

**Protect main branch** (smoke test complete — no more direct pushes needed):
```bash
gh api "repos/$REPO_PATH/branches/main/protection" -X PUT \
  --input - << 'EOF'
{"required_status_checks":null,"enforce_admins":false,
 "required_pull_request_reviews":{"required_approving_review_count":1,"dismiss_stale_reviews":false},
 "restrictions":null}
EOF
```

**Revoke smoke-test PAT** (if local runner was used):
```bash
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
PAT_NAME=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.pat_name 2>/dev/null || echo "")
if [ -n "$PAT_NAME" ]; then
  python3 "$PAT_OPS" revoke --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT" --manifest "$MANIFEST"
  gh secret delete SNOWFLAKE_PAT --repo "$REPO_PATH"
  gh secret delete SNOWFLAKE_USER --repo "$REPO_PATH"
else
  echo "No PAT in manifest — skipping PAT revocation"
fi
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_5
```

### What we did
- Smoke-test reverted — cleanup workflow triggered
- Main branch protected (PR reviews required)
- PAT revoked from Keychain and SNOWFLAKE_PAT secret removed
