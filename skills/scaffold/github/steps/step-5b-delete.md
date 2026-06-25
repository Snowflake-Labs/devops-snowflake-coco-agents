# Step 6b: Delete Repo + Local Clone (GitHub)

> Sub-step of Step 6. Only executes for "tear down everything" mode.

```bash
gh repo delete "$REPO_PATH" --yes
[ -z "$REPO_NAME" ] && { echo "Error: REPO_NAME is empty — aborting."; exit 1; }
rm -rf "$REPO_NAME"
rm -rf ".coco-agent/$REPO_NAME" 2>/dev/null
rmdir ".coco-agent" 2>/dev/null || true
echo "✓ $REPO_NAME removed — environment is clean"
```

### What we did

- CI disabled
- Snowflake objects dropped: `$SF_USER / $SF_WH / $SF_ROLE`
- Repo deleted and local clone removed

> ✓ **Done:** Environment is clean.
