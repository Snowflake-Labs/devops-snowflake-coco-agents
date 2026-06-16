# Step 6a: Teardown Snowflake + Runner (GitHub)

> Sub-step of Step 6. Executes after user confirms teardown.
> Read manifest values from step-6 router before loading this sub-step.

**Disable Actions:**

```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'
```

**Stop and deregister runner** (if running):

```bash
if [ "${RUNNER_PID:-0}" -gt 0 ]; then kill "$RUNNER_PID" 2>/dev/null || true; sleep 2; fi
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
fi
```

**[Drop Snowflake only] Restore workflows before disabling:**

```bash
if [ "$TEARDOWN_MODE" = "snowflake-only" ]; then
  sed -i '' 's/runs-on: \[self-hosted, local\]/runs-on: ubuntu-latest/g' \
    "$REPO_NAME/.github/workflows/cortex-scan.yml" \
    "$REPO_NAME/.github/workflows/cortex-fix.yml"
  git -C "$REPO_NAME" add .github/workflows/
  git -C "$REPO_NAME" commit -m "ci(workflows): restore ubuntu-latest runner [skip ci]"
  git -C "$REPO_NAME" push
fi
```

Load `shared/snowflake-drop-sql.md` and execute guard + DROP with values:

- `$SF_USER`, `$SF_WH`, `$SF_ROLE` from manifest

```bash
# No PAT to revoke — OIDC-only auth since Jun 16 cleanup
```
