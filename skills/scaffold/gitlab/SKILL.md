---
name: scaffold-for-gitlab
description: >
  Guided 6-beat scaffold: set up a new GitLab CI CoCo agent project from
  the gitlab-coco-agent template. Provisions Snowflake OIDC resources, sets
  GitLab CI/CD variables, and optionally pushes a sample app to trigger the
  scan->issue->fix automation loop end-to-end.
  Use when the user chose the GitLab path, or invoked
  $devops-coco-agents:scaffold-for-gitlab directly.
---

## Beat Order Rule

⚠️ MANDATORY: Execute beats 1–6 in order. Never skip or reorder.
Each beat builds on the previous — jumping ahead leaves the project in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template project (`https://gitlab.com/kameshsampath/gitlab-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set CI/CD variables other than the four listed in Beat 4.
- Do not enable pipelines before Beat 4 is complete.

## Prerequisites Check

Run both checks before collecting any inputs.

**Check 1 — glab CLI:**
```bash
glab auth status 2>&1
```
If not authenticated:
```
ask_user_question:
  header: "glab CLI required"
  question: "glab is not authenticated. Install glab (https://gitlab.com/gitlab-org/cli) and run 'glab auth login', then come back."
  options:
    - label: "Done, I've authenticated"
    - label: "Abort"
```
Re-run `glab auth status` after "Done" — only continue when it passes.

**Check 2 — snow CLI connection:**
```bash
snow connection test
```
If it fails:
```
ask_user_question:
  header: "snow CLI required"
  question: "Snowflake CLI connection failed. Configure a connection in ~/.snowflake/connections.toml, then come back."
  options:
    - label: "Done, connection works"
    - label: "Abort"
```

## Stopping Points

Collect all four values before Beat 1.

1. **Target project** (`PROJECT_PATH`) — detect GitLab username:
   ```bash
   glab api user --field username
   ```
   Then ask:
   ```
   ask_user_question:
     header: "New project"
     question: "Full path for the new project? (e.g. mygroup/my-coco-agent)"
     type: text
     defaultValue: "<detected-username>/my-coco-agent"
   ```

2. **Snowflake prefix** (`PREFIX`) — ask:
   ```
   ask_user_question:
     header: "Prefix"
     question: "Snowflake resource prefix? All objects will be named PREFIX_GITLAB_COCO_AGENT_*"
     type: text
     defaultValue: "DEMO"
   ```

3. **Snowflake account** (`SNOWFLAKE_ACCOUNT`) — check env first; if unset, ask.

4. **GitLab bot token** (`GITLAB_TOKEN_coco`) — ask:
   ```
   ask_user_question:
     header: "GitLab token"
     question: "GitLab PAT for the bot service account (needs api + write_repository scope). Stored as masked CI/CD variable."
     type: text
     defaultValue: ""
   ```

Derive group and project name for later:
```
GROUP="${PROJECT_PATH%/*}"
PROJECT_NAME="${PROJECT_PATH##*/}"
ENCODED_PATH=$(python3 -c "import urllib.parse,os; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")
```

---

## Beat 1 — Scaffold project from template

**What I'll do:**
Create `$PROJECT_PATH` from the `gitlab-coco-agent` template and clone it locally.

Enter plan mode and present:
```
Creates: $PROJECT_PATH (from https://gitlab.com/kameshsampath/gitlab-coco-agent)
Clones:  ./$PROJECT_NAME
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 1"
  question: "Create project $PROJECT_PATH from the gitlab-coco-agent template?"
  options:
    - label: "Create and clone"
    - label: "Show me the template first"
      description: "Preview https://gitlab.com/kameshsampath/gitlab-coco-agent"
    - label: "Abort"
```

If "Show me the template first": run `glab repo view https://gitlab.com/kameshsampath/gitlab-coco-agent`, then re-ask.

Execute:
```bash
glab project create "$PROJECT_NAME" \
  --group "$GROUP" \
  --template-project https://gitlab.com/kameshsampath/gitlab-coco-agent

glab repo clone "$PROJECT_PATH"
```

**What we did:**
- Project created at `https://gitlab.com/$PROJECT_PATH`
- Local clone in `./$PROJECT_NAME`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 1 done"
  question: "Project created and cloned. Continue to Beat 2 (disable pipelines + repo init)?"
  options:
    - label: "Yes, continue to Beat 2"
    - label: "Replay Beat 1"
    - label: "Stop here"
```

---

## Beat 2 — Repo Init (disable pipelines)

**What I'll do:**
Disable CI/CD pipelines on the new project so no jobs trigger during setup.
Pipelines will be re-enabled in Beat 5 when everything is ready.

```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
```

**What we did:**
Pipelines disabled. No CI jobs will fire until setup is complete.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 2 done"
  question: "Pipelines disabled. Continue to Beat 3 (provision Snowflake OIDC user)?"
  options:
    - label: "Yes, continue to Beat 3"
    - label: "Replay Beat 2"
    - label: "Stop here"
```

---

## Beat 3 — Provision Snowflake OIDC user

**What I'll do:**
Read `$PROJECT_NAME/snowflake/setup.sql` to confirm the SQL, then execute it.
Note: the GitLab setup SQL requires `--enable-templating STANDARD`.

Enter plan mode and present:
```
Creates (idempotent — safe to re-run):
  Role:      ${PREFIX}_GITLAB_COCO_AGENT_ROLE
  Warehouse: ${PREFIX}_GITLAB_COCO_AGENT_WH  (XS, auto-suspend 60s)
  User:      ${PREFIX}_GITLAB_COCO_AGENT_USER
             TYPE = WORKLOAD_IDENTITY
             OIDC issuer: https://gitlab.com
             Subject: project_path:$PROJECT_PATH:ref_type:branch:ref:main

Command:
  snow sql -f $PROJECT_NAME/snowflake/setup.sql \
    -D "PREFIX=$PREFIX" -D "REPO_PATH=$PROJECT_PATH" \
    --enable-templating STANDARD
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 3"
  question: "Provision Snowflake OIDC resources?"
  options:
    - label: "Yes, provision"
    - label: "Show setup.sql first"
    - label: "Stop here"
```

If "Show setup.sql first": read and display `$PROJECT_NAME/snowflake/setup.sql`, then re-ask.

Execute:
```bash
snow sql -f "$PROJECT_NAME/snowflake/setup.sql" \
  -D "PREFIX=$PREFIX" \
  -D "REPO_PATH=$PROJECT_PATH" \
  --enable-templating STANDARD
```

**Verify** the user was created:
```bash
snow sql -q "DESC USER ${PREFIX}_GITLAB_COCO_AGENT_USER" --format json 2>&1
```
If DESC fails: "Setup SQL may have failed. Check the output above and re-run Beat 3."

**What we did:**
Snowflake role, warehouse, and WORKLOAD_IDENTITY user provisioned and verified.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 3 done"
  question: "Snowflake resources ready. Continue to Beat 4 (set CI/CD variables)?"
  options:
    - label: "Yes, continue to Beat 4"
    - label: "Replay Beat 3"
    - label: "Stop here"
```

---

## Beat 4 — Set GitLab CI/CD variables

**What I'll do:**
Set the four CI/CD variables the pipeline jobs need. Sensitive values are masked.

Enter plan mode:
```
Variable              Value                                  Masked
──────────────────── ────────────────────────────────────── ──────
SNOWFLAKE_ACCOUNT    $SNOWFLAKE_ACCOUNT                     yes
SNOWFLAKE_USER       ${PREFIX}_GITLAB_COCO_AGENT_USER       no
SNOWFLAKE_WAREHOUSE  ${PREFIX}_GITLAB_COCO_AGENT_WH         no
GITLAB_TOKEN_coco    (provided token)                       yes
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 4"
  question: "Set these four CI/CD variables on $PROJECT_PATH?"
  options:
    - label: "Yes, set variables"
    - label: "Stop here"
```

Execute:
```bash
cd "$PROJECT_NAME"
glab variable set SNOWFLAKE_ACCOUNT   --value "$SNOWFLAKE_ACCOUNT"   --masked
glab variable set SNOWFLAKE_USER      --value "${PREFIX}_GITLAB_COCO_AGENT_USER"
glab variable set SNOWFLAKE_WAREHOUSE --value "${PREFIX}_GITLAB_COCO_AGENT_WH"
glab variable set GITLAB_TOKEN_coco   --value "$GITLAB_TOKEN_coco"   --masked
```

**What we did:**
4 CI/CD variables set. Pipelines can now authenticate to Snowflake via OIDC.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 4 done"
  question: "Variables set. Want to test the workflow with a sample app?"
  options:
    - label: "Yes, push demo app and watch the loop"
      description: "Copies a 3-issue Python app into demo/, enables pipelines, commits and pushes"
    - label: "No, I'll push my own code later"
      description: "Re-enable pipelines with: glab api projects/$ENCODED_PATH -X PUT -F builds_access_level=enabled"
    - label: "Stop here"
```

---

## Beat 5 — Demo test (optional)

Only execute if user chose "Yes, push demo app" in Beat 4.

**What I'll do:**
Copy the sample app (3 intentional issues) into `demo/`, enable pipelines,
commit and push. The scan-code job will trigger automatically.

**Step 1 — Copy templates:**
Read from `skills/scaffold/templates/` and write to `$PROJECT_NAME/demo/`:
- `skills/scaffold/templates/app.py` → `$PROJECT_NAME/demo/app.py`
- `skills/scaffold/templates/pyproject.toml` → `$PROJECT_NAME/demo/pyproject.toml`
- `skills/scaffold/templates/tests/__init__.py` → `$PROJECT_NAME/demo/tests/__init__.py`
- `skills/scaffold/templates/tests/test_app.py` → `$PROJECT_NAME/demo/tests/test_app.py`

**Step 2 — Enable pipelines:**
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```

**Step 3 — Commit and push:**
```bash
cd "$PROJECT_NAME"
git add demo/
git commit -m "feat(demo): add intentional-issue app for scan/fix workflow"
git push
```

**Step 4 — Trigger pipeline and show URL:**
```bash
glab pipeline run --branch main
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
```

**What's happening:**
> The `scan-code` job reads `demo/app.py` and creates `[coco-agent]` issues for:
> 1. Hardcoded schema (`SCHEMA = "PUBLIC"` — should use env var)
> 2. Password auth — should use `WORKLOAD_IDENTITY` or `externalbrowser`
> 3. SQL injection — f-string in `cur.execute()`, should use parameterized query
>
> Each issue triggers the `coco-agent` fix job via the GitLab Duo Agent Platform.
> Cortex applies the minimal fix, opens a branch, and creates an MR.

⚠️ MANDATORY pause (repeatable until satisfied):
```
ask_user_question:
  header: "Beat 5"
  question: "Check for issues and MRs?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Stop here"
```

If "Check now":
```bash
echo "=== Issues ===" && glab issue list --label coco-agent
echo "=== MRs ===" && glab mr list --state opened
```

---

## Beat 6 — Teardown (optional)

```
ask_user_question:
  header: "Beat 6"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources and delete the GitLab project"
    - label: "Drop Snowflake only"
    - label: "Keep everything"
```

⚠️ BILLABLE + DESTRUCTIVE. Enter plan mode and present what will be dropped, then ask
for final confirmation before executing:

```bash
snow sql -f "$PROJECT_NAME/snowflake/teardown.sql" \
  -D "PREFIX=$PREFIX" \
  --enable-templating STANDARD

glab project delete "$PROJECT_PATH" --yes
```
