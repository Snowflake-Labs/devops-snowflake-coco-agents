# Step 5b: Revert, Protect, Revoke (GitLab)

> Sub-step of Step 5. Load after smoke test is confirmed done.

**Revert smoke-test commit** (push triggers cleanup run):
```bash
cd "$PROJECT_NAME" && git revert HEAD --no-edit && git push
```

**Protect main branch** (smoke test complete — no more direct pushes needed):
```bash
glab api "projects/$ENCODED_PATH/protected_branches" \
  -X POST -F name=main -F push_access_level=0 -F merge_access_level=40
```

**Revoke smoke-test PAT** (if local runner was used):
```bash
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
PAT_NAME=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key snowflake.pat_name 2>/dev/null || echo "")
if [ -n "$PAT_NAME" ]; then
  python3 "$PAT_OPS" revoke --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT" --manifest "$MANIFEST"
  _v() { local K=$1
    glab api "projects/$ENCODED_PATH/variables/$K" --method DELETE 2>/dev/null && echo "Deleted $K"; }
  _v SNOWFLAKE_PAT
  _v SNOWFLAKE_USER
else
  echo "No PAT in manifest — skipping PAT revocation"
fi
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_5
```

### What we did
- Smoke-test reverted — cleanup pipeline triggered
- Main branch protected (MR reviews required, push restricted)
- PAT revoked from Keychain and SNOWFLAKE_PAT variable removed
