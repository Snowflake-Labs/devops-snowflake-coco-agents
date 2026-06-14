# Step 6b: Delete Project + Local Clone (GitLab)

> Sub-step of Step 6. Only executes for "tear down everything" mode.

```bash
glab project delete "$PROJECT_PATH" --yes
rm -rf "$PROJECT_NAME"
rm -rf ".coco-agent/$PROJECT_NAME" 2>/dev/null
rmdir ".coco-agent" 2>/dev/null || true
echo "✓ $PROJECT_NAME removed — environment is clean"
```

### What we did
- Pipelines disabled, runner stopped and deregistered
- Snowflake objects dropped: `$SF_USER / $SF_WH / $SF_ROLE`
- Project deleted and local clone removed

> ✓ **Done:** Environment is clean.
