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

After the shared step pushes demo/, verify CI triggered and watch the loop:

```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
glab pipeline list --project "$PROJECT_PATH" 2>&1 | head -5
```

⚠️ MANDATORY pause (repeatable):

```
ask_user_question:
  header: "Watch the Loop"
  question: "Check for issues and MRs on $PROJECT_PATH?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Done — continue to revert"
```

If "Check now": `glab issue list --label coco-agent` and `glab mr list --state opened`

When done, load `gitlab/steps/step-5c-verify-smart-fix.md`.
