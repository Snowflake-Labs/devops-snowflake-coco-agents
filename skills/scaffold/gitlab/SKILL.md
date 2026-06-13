---
name: scaffold/gitlab
description: >
  Guided 5-beat scaffold: set up a new project from the gitlab-coco-agent template,
  provision Snowflake OIDC resources, set GitLab CI/CD variables, and run the
  scan->issue->fix automation loop end-to-end.
  Use when the user chose the GitLab path from the scaffold skill.
---

## Beat Order Rule

⚠️ MANDATORY: Execute beats 1–5 in order. Never skip or reorder.
Each beat builds on the previous one. The automation loop only makes sense
end-to-end — jumping ahead leaves the project in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template project (`https://gitlab.com/kameshsampath/gitlab-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set CI/CD variables other than the four listed in Beat 3.
- Do not commit or push to the new project — the CI jobs do that.

## Stopping Points

Collect all four values before starting Beat 1. Auto-detect where possible;
ask only for what cannot be inferred.

1. **Target project** (`PROJECT_PATH`) — detect the user's GitLab username:
   ```bash
   glab api user --field username
   ```
   Then ask:
   ```
   ask_user_question:
     header: "New project"
     question: "Full path for the new project? (e.g. mygroup/my-coco-demo)"
     type: text
     defaultValue: "<detected-username>/my-coco-demo"
   ```

2. **Snowflake prefix** (`PREFIX`) — ask:
   ```
   ask_user_question:
     header: "Prefix"
     question: "Snowflake resource prefix? All objects will be named PREFIX_GITLAB_COCO_AGENT_*"
     type: text
     defaultValue: "DEMO"
   ```

3. **Snowflake account** (`SNOWFLAKE_ACCOUNT`) — check `$SNOWFLAKE_ACCOUNT` env first.
   If unset, ask:
   ```
   ask_user_question:
     header: "Account"
     question: "Snowflake account identifier? (e.g. xy12345.us-east-1)"
     type: text
     defaultValue: ""
   ```

4. **GitLab bot token** (`GITLAB_TOKEN_coco`) — ask:
   ```
   ask_user_question:
     header: "GitLab token"
     question: "GitLab PAT for the bot service account (needs api + write_repository scope). This will be stored as a masked CI/CD variable."
     type: text
     defaultValue: ""
   ```

---

## Beat 1 — Scaffold project from template

**What I'll do:**
Create a new GitLab project at `$PROJECT_PATH` from the
`https://gitlab.com/kameshsampath/gitlab-coco-agent` template. The new project includes the
scan + fix pipeline, Snowflake setup SQL, cortex prompts, and an intentional-issue app.

Derive group and project name:
```
GROUP="${PROJECT_PATH%/*}"
PROJECT_NAME="${PROJECT_PATH##*/}"
```

Enter plan mode and present this summary, then exit and ask:

```
ask_user_question:
  header: "Beat 1"
  question: "Create project $PROJECT_PATH from https://gitlab.com/kameshsampath/gitlab-coco-agent?"
  options:
    - label: "Create and clone"
      description: "Runs glab project create --template-project, then clones locally"
    - label: "Show me the template first"
      description: "Preview what's in the template before creating"
    - label: "Abort"
      description: "Stop here"
```

If "Show me the template first": run `glab repo view https://gitlab.com/kameshsampath/gitlab-coco-agent`
and display the description, then re-ask.

If "Create and clone":
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
  question: "Project created and cloned. Continue to Beat 2 (provision Snowflake)?"
  options:
    - label: "Yes, continue to Beat 2"
    - label: "Replay Beat 1"
      description: "Something went wrong — re-run the create step"
    - label: "Stop here"
```

---

## Beat 2 — Provision Snowflake resources

**What I'll do:**
Read `$PROJECT_NAME/snowflake/setup.sql` to confirm variable names, then run it
to create the role, warehouse, and WORKLOAD_IDENTITY user bound to this project.

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
    -D "PREFIX=$PREFIX" \
    -D "REPO_PATH=$PROJECT_PATH" \
    --enable-templating STANDARD
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 2"
  question: "Provision these Snowflake resources?"
  options:
    - label: "Yes, provision"
    - label: "Show setup.sql first"
      description: "Review the SQL before running"
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

**What we did:**
Snowflake role, warehouse, and WORKLOAD_IDENTITY user provisioned.
The GitLab CI OIDC token for `$PROJECT_PATH` main branch is now trusted.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 2 done"
  question: "Snowflake resources ready. Continue to Beat 3 (set CI/CD variables)?"
  options:
    - label: "Yes, continue to Beat 3"
    - label: "Replay Beat 2"
      description: "Re-run setup.sql"
    - label: "Stop here"
```

---

## Beat 3 — Set GitLab CI/CD variables

**What I'll do:**
Set the four CI/CD variables the scan and fix jobs need. Sensitive values
are stored masked. No password is stored — Snowflake authentication uses
WORKLOAD_IDENTITY via OIDC.

Enter plan mode and present the variable table:
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
  header: "Beat 3"
  question: "Set these four CI/CD variables on $PROJECT_PATH?"
  options:
    - label: "Yes, set variables"
    - label: "Stop here"
```

Execute (cd into the cloned project first so glab targets the right project):
```bash
cd "$PROJECT_NAME"
glab variable set SNOWFLAKE_ACCOUNT   --value "$SNOWFLAKE_ACCOUNT"   --masked
glab variable set SNOWFLAKE_USER      --value "${PREFIX}_GITLAB_COCO_AGENT_USER"
glab variable set SNOWFLAKE_WAREHOUSE --value "${PREFIX}_GITLAB_COCO_AGENT_WH"
glab variable set GITLAB_TOKEN_coco   --value "$GITLAB_TOKEN_coco"   --masked
```

**What we did:**
4 CI/CD variables set. The scan and fix jobs can now authenticate to Snowflake
(OIDC path) and to GitLab (bot token for issue/MR operations).

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 3 done"
  question: "Variables set. Trigger the first scan to start the automation?"
  options:
    - label: "Yes, trigger scan"
    - label: "Replay Beat 3"
      description: "Re-set the variables"
    - label: "Stop here"
```

---

## Beat 4 — Trigger scan and watch the loop

**What I'll do:**
Trigger the `scan-code` CI job on main. Cortex will read `demo/app.py`,
find the 3 intentional bugs, and create GitLab issues titled `[coco-agent] Bug: ...`.
Each issue triggers the `coco-agent` fix job (via GitLab Duo Agent Platform),
which fixes the bug and opens an MR.

```bash
cd "$PROJECT_NAME" && glab pipeline run --branch main
```

Then show the pipelines URL:
```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
```

**What's happening:**

> The scan job asks Cortex to review `demo/app.py` and create issues for:
> 1. Hardcoded schema (`SCHEMA = "PUBLIC"` — should use env var)
> 2. Password auth (should use `WORKLOAD_IDENTITY` or `externalbrowser`)
> 3. SQL injection (f-string in `cur.execute()` — should use parameterized query)
>
> Each `[coco-agent]` issue triggers the fix job via the GitLab Duo Agent Platform.
> The fix job asks Cortex to apply the minimal fix, commits to a branch,
> and opens an MR that closes the issue.

⚠️ MANDATORY pause (offer to check status on demand):
```
ask_user_question:
  header: "Beat 4"
  question: "Scan triggered. Check for issues and MRs?"
  options:
    - label: "Check now"
      description: "List open [coco-agent] issues and MRs"
    - label: "Not done yet — wait"
      description: "Come back when the scan pipeline completes"
    - label: "Stop here"
```

If "Check now":
```bash
echo "=== Issues ===" && glab issue list --label coco-agent
echo "=== MRs ===" && glab mr list --state opened
```
If nothing yet: "Still running — come back in a minute and check again."
Re-offer the same question until the user is satisfied.

---

## Beat 5 — Teardown (optional)

**What we achieved:**
The scan->fix loop ran end-to-end:
push -> scan pipeline -> [coco-agent] issues -> fix pipeline -> MRs

Ask whether to clean up:

```
ask_user_question:
  header: "Beat 5"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources and delete the GitLab project"
    - label: "Drop Snowflake only"
      description: "Keep the project, drop role/warehouse/user"
    - label: "Keep everything"
      description: "Leave the project and Snowflake resources as-is"
```

⚠️ BILLABLE + DESTRUCTIVE: Confirm before executing teardown.

Enter plan mode and present:
```
Will drop:
  ${PREFIX}_GITLAB_COCO_AGENT_USER
  ${PREFIX}_GITLAB_COCO_AGENT_WH
  ${PREFIX}_GITLAB_COCO_AGENT_ROLE

Will delete GitLab project: $PROJECT_PATH (IRREVERSIBLE)
```

Exit plan mode, ask one final confirmation, then execute:

```bash
# Drop Snowflake resources
snow sql -f "$PROJECT_NAME/snowflake/teardown.sql" \
  -D "PREFIX=$PREFIX" \
  --enable-templating STANDARD

# Delete GitLab project (only if user chose "tear down everything")
glab project delete "$PROJECT_PATH" --yes
```
