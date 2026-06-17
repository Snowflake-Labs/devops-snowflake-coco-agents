# Step 5a: Smoke Test (GitLab)

> Sub-step of Step 5. Enables pipelines then loads the shared generation flow.
> Set `REPO_OR_PROJECT_NAME="$PROJECT_NAME"` before loading the shared step.
> `_j()` helper is defined in earlier steps — available in scope.

**Enable pipelines:**

```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```

**Verify:** `glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"` → `enabled`.

```bash
REPO_OR_PROJECT_NAME="$PROJECT_NAME"
```

Load `shared/generate-demo.md`.

After the shared step pushes demo/, watch the pipeline live:

```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"

# Live TUI view — refreshes automatically until pipeline completes.
# Note: 'ci' namespace is deprecated; equivalent to 'glab pipeline status --live'
glab ci status --live

# Show results once pipeline finishes
glab issue list --label coco-agent
glab mr list --state opened
```

When done, load `gitlab/steps/step-5c-verify-smart-fix.md`.
