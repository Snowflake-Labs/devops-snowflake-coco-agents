# Step 5b: Revert and Protect (GitHub)

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

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_5
```

### What we did

- Smoke-test reverted — cleanup workflow triggered
- Main branch protected (PR reviews required)
