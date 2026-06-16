# Step 6a: Teardown Snowflake + Runner (GitLab)

> Sub-step of Step 6. Executes after user confirms teardown.
> Read manifest values from step-6 router before loading this sub-step.

**Disable pipelines:**

```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
```

**Stop and deregister runner** (if running):

```bash
if [ "${RUNNER_PID:-0}" -gt 0 ]; then kill "$RUNNER_PID" 2>/dev/null || true; sleep 2; fi
if [ -n "$RUNNER_ID" ] && [ "$RUNNER_ID" != "0" ]; then
  glab api "projects/$ENCODED_PATH/runners/$RUNNER_ID" -X DELETE
fi
```

**[Drop Snowflake only] Restore pipeline before disabling:**

```bash
if [ "$TEARDOWN_MODE" = "snowflake-only" ]; then
  python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)\n  tags: \[local\]", rf"\1", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Reverted: tags: [local] removed")
PYEOF
  git -C "$PROJECT_NAME" add .gitlab-ci.yml
  git -C "$PROJECT_NAME" commit -m "ci: restore default runner [skip ci]"
  git -C "$PROJECT_NAME" push
fi
```

Load `shared/snowflake-drop-sql.md` and execute guard + DROP with values:

- `$SF_USER`, `$SF_WH`, `$SF_ROLE` from manifest

```bash
# No PAT to revoke — OIDC-only auth since Jun 16 cleanup
```
