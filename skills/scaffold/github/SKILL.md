---
name: scaffold/github
description: >
  Guided 5-beat scaffold: set up a new repo from the github-coco-agent template,
  provision Snowflake OIDC resources, set GitHub secrets, and run the
  scan->issue->fix automation loop end-to-end.
  Use when the user chose the GitHub path from the scaffold skill.
---

## Beat Order Rule

⚠️ MANDATORY: Execute beats 1–5 in order. Never skip or reorder.
Each beat builds on the previous one. The automation loop only makes sense
end-to-end — jumping ahead leaves the repo in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template repo (`https://github.com/Snowflake-Labs/github-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set GitHub secrets other than the three listed in Beat 3.
- Do not commit or push to the new repo — the CI workflows do that.

## Stopping Points

Collect all three values before starting Beat 1. Auto-detect where possible;
ask only for what cannot be inferred.

1. **Target repo** (`REPO_PATH`) — detect the user's GitHub login:
   ```bash
   gh api user --jq .login
   ```
   Then ask:
   ```
   ask_user_question:
     header: "New repo"
     question: "Full name for the new repo? (e.g. myorg/my-coco-demo)"
     type: text
     defaultValue: "<detected-login>/my-coco-demo"
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
Create `$REPO_PATH` as a public GitHub repo from the `github-coco-agent`
template and clone it locally. The new repo includes the scan + fix workflows,
Snowflake setup SQL, cortex prompts, and an intentional-issue app — ready to use.

Enter plan mode and present this summary, then exit and ask:

```
ask_user_question:
  header: "Beat 1"
  question: "Create repo $REPO_PATH from https://github.com/Snowflake-Labs/github-coco-agent?"
  options:
    - label: "Create and clone"
      description: "Runs gh repo create --template, then clones locally"
    - label: "Show me the template first"
      description: "Preview what's in the template before creating"
    - label: "Abort"
      description: "Stop here"
```

If "Show me the template first": run `gh repo view https://github.com/Snowflake-Labs/github-coco-agent`
and display the description + file tree, then re-ask.

If "Create and clone":
```bash
gh repo create "$REPO_PATH" \
  --template https://github.com/Snowflake-Labs/github-coco-agent \
  --public \
  --clone
```

**What we did:**
- Repo created at `$(gh repo view $REPO_PATH --json url -q .url)`
- Local clone in `./$REPO_NAME` (last segment of `$REPO_PATH`)

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 1 done"
  question: "Repo created and cloned. Continue to Beat 2 (provision Snowflake)?"
  options:
    - label: "Yes, continue to Beat 2"
    - label: "Replay Beat 1"
      description: "Something went wrong — re-run the create step"
    - label: "Stop here"
```

---

## Beat 2 — Provision Snowflake resources

**What I'll do:**
Read `$REPO_NAME/snowflake/setup.sql` to confirm variable names, then run it
to create the role, warehouse, and WORKLOAD_IDENTITY user bound to this repo.

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
    -D "PREFIX=$PREFIX" \
    -D "REPO_PATH=$REPO_PATH"
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

If "Show setup.sql first": read and display `$REPO_NAME/snowflake/setup.sql`, then re-ask.

Execute:
```bash
snow sql -f "$REPO_NAME/snowflake/setup.sql" \
  -D "PREFIX=$PREFIX" \
  -D "REPO_PATH=$REPO_PATH"
```

**What we did:**
Snowflake role, warehouse, and WORKLOAD_IDENTITY user provisioned.
The GitHub Actions OIDC token for `$REPO_PATH` main branch is now trusted.

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 2 done"
  question: "Snowflake resources ready. Continue to Beat 3 (set GitHub secrets)?"
  options:
    - label: "Yes, continue to Beat 3"
    - label: "Replay Beat 2"
      description: "Re-run setup.sql"
    - label: "Stop here"
```

---

## Beat 3 — Set GitHub repository secrets

**What I'll do:**
Set the three repository secrets the scan and fix workflows need to authenticate
to Snowflake via OIDC. No password is stored — the WORKLOAD_IDENTITY user
authenticates via a short-lived GitHub JWT.

Enter plan mode and present the secret table:
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
  header: "Beat 3"
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
3 secrets set. The workflows can now authenticate to Snowflake via OIDC
(no long-lived credentials stored).

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 3 done"
  question: "Secrets set. Trigger the first scan to start the automation?"
  options:
    - label: "Yes, trigger scan"
    - label: "Replay Beat 3"
      description: "Re-set the secrets"
    - label: "Stop here"
```

---

## Beat 4 — Trigger scan and watch the loop

**What I'll do:**
Trigger the `cortex-scan` workflow manually. Cortex will read `demo/app.py`,
find the 3 intentional bugs, and create GitHub issues titled `[coco-agent] Bug: ...`.
Each issue automatically triggers the `cortex-fix` workflow, which fixes the bug
and opens a PR.

```bash
cd "$REPO_NAME" && gh workflow run cortex-scan.yml
```

Then show the Actions URL:
```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
```

**What's happening:**

> The scan workflow asks Cortex to review `demo/app.py` and create issues for:
> 1. Hardcoded schema (`SCHEMA = "PUBLIC"` — should use env var)
> 2. Password auth (should use `WORKLOAD_IDENTITY` or `externalbrowser`)
> 3. SQL injection (f-string in `cur.execute()` — should use parameterized query)
>
> Each `[coco-agent]` issue triggers the fix workflow automatically.
> The fix workflow asks Cortex to apply the minimal fix, commits to a branch,
> and opens a PR with `--auto --squash`.

⚠️ MANDATORY pause (offer to check status on demand):
```
ask_user_question:
  header: "Beat 4"
  question: "Scan triggered. Check for issues and PRs?"
  options:
    - label: "Check now"
      description: "List open [coco-agent] issues and PRs"
    - label: "Not done yet — wait"
      description: "Come back when the scan workflow completes"
    - label: "Stop here"
```

If "Check now":
```bash
echo "=== Issues ===" && gh issue list --repo "$REPO_PATH" --label coco-agent
echo "=== PRs ===" && gh pr list --repo "$REPO_PATH" --state open
```
If nothing yet: "Still running — come back in a minute and check again."
Re-offer the same question until the user is satisfied.

---

## Beat 5 — Teardown (optional)

**What we achieved:**
The scan->fix loop ran end-to-end:
push -> scan workflow -> [coco-agent] issues -> fix workflow -> PRs

Ask whether to clean up:

```
ask_user_question:
  header: "Beat 5"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources and delete the GitHub repo"
    - label: "Drop Snowflake only"
      description: "Keep the repo, drop role/warehouse/user"
    - label: "Keep everything"
      description: "Leave the repo and Snowflake resources as-is"
```

⚠️ BILLABLE + DESTRUCTIVE: Confirm before executing teardown.

Enter plan mode and present:
```
Will drop:
  ${PREFIX}_GITHUB_COCO_AGENT_USER
  ${PREFIX}_GITHUB_COCO_AGENT_WH
  ${PREFIX}_GITHUB_COCO_AGENT_ROLE

Will delete GitHub repo: $REPO_PATH (IRREVERSIBLE)
```

Exit plan mode, ask one final confirmation, then execute:

```bash
# Drop Snowflake resources
snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"

# Delete GitHub repo (only if user chose "tear down everything")
gh repo delete "$REPO_PATH" --yes
```
