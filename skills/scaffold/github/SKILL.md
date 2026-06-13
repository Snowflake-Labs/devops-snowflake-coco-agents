---
name: scaffold-for-github
description: >
  Guided 6-beat scaffold: set up a new GitHub Actions CoCo agent project from
  the github-coco-agent template. Provisions Snowflake OIDC resources, sets
  GitHub secrets, and optionally pushes a sample app to trigger the
  scan->issue->fix automation loop end-to-end.
  Use when the user chose the GitHub path, or invoked
  $devops-coco-agents:scaffold-for-github directly.
---

## Beat Order Rule

⚠️ MANDATORY: Execute beats 1–6 in order. Never skip or reorder.
Each beat builds on the previous — jumping ahead leaves the repo in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template repo (`https://github.com/Snowflake-Labs/github-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set GitHub secrets other than the three listed in Beat 4.
- Do not enable Actions before Beat 4 is complete.

## Prerequisites Check

Run both checks before collecting any inputs. If either fails, stop and help
the user fix it before proceeding.

**Check 1 — gh CLI:**
```bash
gh auth status 2>&1
```
If not authenticated:
```
ask_user_question:
  header: "gh CLI required"
  question: "gh is not authenticated. Install gh (https://cli.github.com) and run 'gh auth login', then come back."
  options:
    - label: "Done, I've authenticated"
      description: "Re-run the check and proceed"
    - label: "Abort"
```
Re-run `gh auth status` after "Done" — only continue when it passes.

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

Collect all three values before Beat 1. Auto-detect where possible.

1. **Target repo** (`REPO_PATH`) — detect GitHub login:
   ```bash
   gh api user --jq .login
   ```
   Then ask:
   ```
   ask_user_question:
     header: "New repo"
     question: "Full name for the new repo? (e.g. myorg/my-coco-agent)"
     type: text
     defaultValue: "<detected-login>/my-coco-agent"
   ```

2. **Snowflake prefix** (`PREFIX`) — ask:
   ```
   ask_user_question:
     header: "Prefix"
     question: "Snowflake resource prefix? All objects will be named PREFIX_GITHUB_COCO_AGENT_*"
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

---

## Beat 1 — Scaffold repo from template

**What I'll do:**
Create `$REPO_PATH` as a public GitHub repo from the `github-coco-agent` template
and clone it locally.

Enter plan mode and present:
```
Creates: $REPO_PATH (public, from https://github.com/Snowflake-Labs/github-coco-agent)
Clones:  ./$REPO_NAME
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 1"
  question: "Create repo $REPO_PATH from the github-coco-agent template?"
  options:
    - label: "Create and clone"
    - label: "Show me the template first"
      description: "Preview https://github.com/Snowflake-Labs/github-coco-agent"
    - label: "Abort"
```

If "Show me the template first": run `gh repo view https://github.com/Snowflake-Labs/github-coco-agent`
and display the description + file tree, then re-ask.

Execute:
```bash
gh repo create "$REPO_PATH" \
  --template https://github.com/Snowflake-Labs/github-coco-agent \
  --public \
  --clone
```

**What we did:**
- Repo created at `$(gh repo view "$REPO_PATH" --json url -q .url)`
- Local clone in `./$REPO_NAME`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 1 done"
  question: "Repo created and cloned. Continue to Beat 2 (disable Actions + repo init)?"
  options:
    - label: "Yes, continue to Beat 2"
    - label: "Replay Beat 1"
    - label: "Stop here"
```

---

## Beat 2 — Repo Init (disable Actions)

**What I'll do:**
Disable GitHub Actions on the new repo so no workflows trigger during setup.
Actions will be re-enabled in Beat 5 when everything is ready.

```bash
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT \
  --input - <<'EOF'
{"enabled": false}
EOF
```

**What we did:**
Actions disabled. No workflows will fire until setup is complete.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 2 done"
  question: "Actions disabled. Continue to Beat 3 (provision Snowflake OIDC user)?"
  options:
    - label: "Yes, continue to Beat 3"
    - label: "Replay Beat 2"
    - label: "Stop here"
```

---

## Beat 3 — Provision Snowflake OIDC user

**What I'll do:**
Read `$REPO_NAME/snowflake/setup.sql` to confirm the SQL, then execute it to create
the role, warehouse, and WORKLOAD_IDENTITY user bound to this repo's main branch.

Enter plan mode and present:
```
Creates (idempotent — safe to re-run):
  Role:      ${PREFIX}_GITHUB_COCO_AGENT_ROLE
  Warehouse: ${PREFIX}_GITHUB_COCO_AGENT_WH  (XS, auto-suspend 60s)
  User:      ${PREFIX}_GITHUB_COCO_AGENT_USER
             TYPE = WORKLOAD_IDENTITY
             OIDC issuer: https://token.actions.githubusercontent.com
             Subject: repo:$REPO_PATH:ref:refs/heads/main

Command:
  snow sql -f $REPO_NAME/snowflake/setup.sql \
    -D "PREFIX=$PREFIX" -D "REPO_PATH=$REPO_PATH"
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

If "Show setup.sql first": read and display `$REPO_NAME/snowflake/setup.sql`, then re-ask.

Execute:
```bash
snow sql -f "$REPO_NAME/snowflake/setup.sql" \
  -D "PREFIX=$PREFIX" \
  -D "REPO_PATH=$REPO_PATH"
```

**Verify** the user was created:
```bash
snow sql -q "DESC USER ${PREFIX}_GITHUB_COCO_AGENT_USER" --format json 2>&1
```
If the DESC fails: "Setup SQL may have failed. Check the output above and re-run Beat 3."

**What we did:**
Snowflake role, warehouse, and WORKLOAD_IDENTITY user provisioned and verified.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 3 done"
  question: "Snowflake resources ready. Continue to Beat 4 (set GitHub secrets)?"
  options:
    - label: "Yes, continue to Beat 4"
    - label: "Replay Beat 3"
    - label: "Stop here"
```

---

## Beat 4 — Set GitHub secrets

**What I'll do:**
Set the three repository secrets the workflows need to authenticate to Snowflake
via OIDC. No password is stored.

Enter plan mode:
```
Secret               Value
──────────────────── ─────────────────────────────────────────
SNOWFLAKE_ACCOUNT    $SNOWFLAKE_ACCOUNT
SNOWFLAKE_ROLE       ${PREFIX}_GITHUB_COCO_AGENT_ROLE
SNOWFLAKE_WAREHOUSE  ${PREFIX}_GITHUB_COCO_AGENT_WH
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 4"
  question: "Set these three secrets on $REPO_PATH?"
  options:
    - label: "Yes, set secrets"
    - label: "Stop here"
```

Execute:
```bash
gh secret set SNOWFLAKE_ACCOUNT   --repo "$REPO_PATH" --body "$SNOWFLAKE_ACCOUNT"
gh secret set SNOWFLAKE_ROLE      --repo "$REPO_PATH" --body "${PREFIX}_GITHUB_COCO_AGENT_ROLE"
gh secret set SNOWFLAKE_WAREHOUSE --repo "$REPO_PATH" --body "${PREFIX}_GITHUB_COCO_AGENT_WH"
```

**What we did:**
3 secrets set. Workflows can now authenticate to Snowflake via OIDC.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 4 done"
  question: "Secrets set. Want to test the workflow with a sample app?"
  options:
    - label: "Yes, push demo app and watch the loop"
      description: "Copies a 3-issue Python app into demo/, enables Actions, commits and pushes"
    - label: "No, I'll push my own code later"
      description: "Actions stay disabled — re-enable with: gh api repos/$REPO_PATH/actions/permissions -X PUT --input - <<<'{\"enabled\":true}'"
    - label: "Stop here"
```

---

## Beat 5 — Demo test (optional)

Only execute if user chose "Yes, push demo app" in Beat 4.

**What I'll do:**
Copy the sample app (3 intentional issues) into `demo/`, enable Actions,
commit and push. The scan workflow will trigger automatically.

**Step 1 — Copy templates:**
Read these files from the skill's templates directory and write them to `$REPO_NAME/demo/`:
- `skills/scaffold/templates/app.py` → `$REPO_NAME/demo/app.py`
- `skills/scaffold/templates/pyproject.toml` → `$REPO_NAME/demo/pyproject.toml`
- `skills/scaffold/templates/tests/__init__.py` → `$REPO_NAME/demo/tests/__init__.py`
- `skills/scaffold/templates/tests/test_app.py` → `$REPO_NAME/demo/tests/test_app.py`

**Step 2 — Enable Actions:**
```bash
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT \
  --input - <<'EOF'
{"enabled": true}
EOF
```

**Step 3 — Commit and push:**
```bash
cd "$REPO_NAME"
git add demo/
git commit -m "feat(demo): add intentional-issue app for scan/fix workflow"
git push
```

**Step 4 — Show Actions URL:**
```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
```

**What's happening:**
> The `cortex-scan` workflow reads `demo/app.py` and creates `[coco-agent]` issues for:
> 1. Hardcoded schema (`SCHEMA = "PUBLIC"` — should use env var)
> 2. Password auth — should use `WORKLOAD_IDENTITY` or `externalbrowser`
> 3. SQL injection — f-string in `cur.execute()`, should use parameterized query
>
> Each issue triggers the `cortex-fix` workflow automatically.
> Cortex applies the minimal fix, opens a branch, and creates a PR.

⚠️ MANDATORY pause (repeatable until satisfied):
```
ask_user_question:
  header: "Beat 5"
  question: "Check for issues and PRs?"
  options:
    - label: "Check now"
    - label: "Not done yet — wait"
    - label: "Stop here"
```

If "Check now":
```bash
echo "=== Issues ===" && gh issue list --repo "$REPO_PATH" --label coco-agent
echo "=== PRs ===" && gh pr list --repo "$REPO_PATH" --state open
```

---

## Beat 6 — Teardown (optional)

```
ask_user_question:
  header: "Beat 6"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources and delete the GitHub repo"
    - label: "Drop Snowflake only"
    - label: "Keep everything"
```

⚠️ BILLABLE + DESTRUCTIVE. Enter plan mode and present what will be dropped, then ask
for final confirmation before executing:

```bash
snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"
gh repo delete "$REPO_PATH" --yes
```
