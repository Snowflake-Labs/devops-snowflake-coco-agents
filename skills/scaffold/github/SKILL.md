---
name: scaffold-for-github
description: >
  Guided 6-step scaffold: set up a new GitHub Actions CoCo agent project from
  the github-coco-agent template. Provisions Snowflake OIDC resources, sets
  GitHub secrets, and optionally pushes a sample app to trigger the
  scan->issue->fix automation loop end-to-end.
  Use when the user chose the GitHub path, or invoked
  $devops-coco-agents:scaffold-for-github directly.
---

## Plan Mode Rule

⚠️ MANDATORY on every step: call `enter_plan_mode` **before** presenting any
content (Why this matters, What we'll do, resource tables, command previews).
Call `exit_plan_mode` immediately after the preview — the `ask_user_question`
that follows is the single confirm gate. Never present step content or run any
command without this pattern.

## Step Order

⚠️ MANDATORY: Execute steps 1–6 in order. Never skip or reorder.
Each step builds on the previous — jumping ahead leaves the repo in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template repo (`https://github.com/Snowflake-Labs/github-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set GitHub secrets other than the three listed in Configure.
- Do not enable Actions before Configure is complete.

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

**Multi-account detection:**
Parse all accounts from `gh auth status 2>&1` by extracting lines matching
`"Logged in to github.com account <name>"` and identifying the one with
`"Active account: true"`.

If only one account is found: proceed silently.

If more than one account is found:
```
ask_user_question:
  header: "GitHub account"
  question: "Multiple GitHub accounts found. Which one should be used for this project?"
  defaultAnswer: "<currently active account>"
  options: [one entry per detected account, label = username]
```
If the chosen account is not the currently active one:
```bash
gh auth switch --user <chosen>
```
Then confirm: `gh api user --jq .login`

> ✓ **Done:** Using GitHub account `<chosen>`.

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

## Run Mode, Project Name, and Output Format

Read `skills/scaffold/references/run-mode.md` (Steps A + B) and
`skills/scaffold/references/output-format.md` (formatting rules)
before collecting any inputs.

## Stopping Points

Collect all three values before Create Project. Auto-detect where possible.

1. **Target repo** (`REPO_PATH`) — detect GitHub login:
   ```bash
   gh api user --jq .login
   ```
   Use the petname from Step B of `run-mode.md` as the `defaultValue`.
   Track the generated name as `GENERATED_PETNAME` for conflict detection.

   ```
   ask_user_question:
     header: "New repo"
     question: "Name for the new repo? (generated suggestion — edit freely)"
     type: text
     defaultValue: "<detected-login>/<generated-petname>"
   ```

   After the user answers, compare the submitted value to `<detected-login>/<GENERATED_PETNAME>`.
   If they match: `USING_GENERATED = true`. If different: `USING_GENERATED = false`.

2. **Visibility** (`REPO_VISIBILITY`) — detect if owner is an org:
   ```bash
   OWNER="${REPO_PATH%%/*}"
   gh api "orgs/$OWNER" 2>/dev/null && IS_ORG=true || IS_ORG=false
   ```
   If personal account (IS_ORG=false):
   ```
   ask_user_question:
     header: "Visibility"
     question: "Repo visibility? (private is recommended)"
     defaultAnswer: "Private"
     options:
       - label: "Private"
         description: "Only you and collaborators can access it"
       - label: "Public"
         description: "Visible to everyone on GitHub"
   ```
   If org account (IS_ORG=true):
   ```
   ask_user_question:
     header: "Visibility"
     question: "Repo visibility? (private is recommended)"
     defaultAnswer: "Private"
     options:
       - label: "Private"
         description: "Only org members with access can see it"
       - label: "Internal"
         description: "Visible to all members of your GitHub organization"
       - label: "Public"
         description: "Visible to everyone on GitHub"
   ```
   Store as `$REPO_VISIBILITY`. Flag mapping: Private → `--private`, Internal → `--internal`, Public → `--public`.

3. **Snowflake prefix** (`PREFIX`) — detect from current Snowflake user:
   ```bash
   snow sql -q "SELECT CURRENT_USER()" --format json \
     | python3 -c "import sys,json; u=list(json.load(sys.stdin)[0].values())[0]; print(u.split('@')[0].upper()[:10])"
   ```
   Then ask:
   ```
   ask_user_question:
     header: "Prefix"
     question: "Snowflake resource prefix? All objects will be named PREFIX_GITHUB_COCO_AGENT_*"
     type: text
     defaultValue: "<detected-snowflake-user>"
   ```

4. **Snowflake account** (`SNOWFLAKE_ACCOUNT`) — check `$SNOWFLAKE_ACCOUNT` env first.
   If unset, ask:
   ```
   ask_user_question:
     header: "Account"
     question: "Snowflake account identifier? (e.g. xy12345.us-east-1)"
     type: text
     defaultValue: ""
   ```

---

## Create Project

**Pre-step guard — check remote does not already exist:**
```bash
gh api "repos/$REPO_PATH" 2>&1
```

If the repo EXISTS and `USING_GENERATED = true` (conflict on generated name):
- Generate a new petname (see `output-format.md` rotation rules)
- > ℹ️ **Note:** `$REPO_PATH` is already taken — here's a fresh suggestion.
- Re-present the name question with new `defaultValue`
- Repeat up to 3 times; after 3 failures set `USING_GENERATED = false` and ask user to type their own

If the repo EXISTS and `USING_GENERATED = false` (user-supplied name conflict):
```
ask_user_question:
  header: "Repo exists"
  question: "`$REPO_PATH` already exists on GitHub. What would you like to do?"
  options:
    - label: "Use the existing repo"
      description: "Skip creation, clone it, and proceed to Hold Before Go-Live"
    - label: "Choose a different name"
      description: "Pick a new name and retry this step"
    - label: "Abort"
```

If "Use the existing repo":
```bash
git clone "https://github.com/$REPO_PATH.git" "$REPO_NAME"
```

Then run state detection to find where to resume:
```bash
echo "=== Detecting completed steps ==="
# Step 2: Actions state
S2=$(gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled 2>/dev/null)
# Step 3: OIDC user exists?
S3=$(snow sql -q "SHOW USERS LIKE '${PREFIX}_GITHUB_COCO_AGENT_USER'" \
       --format json 2>/dev/null \
       | python3 -c "import sys,json; print('done' if json.load(sys.stdin) else '')" 2>/dev/null)
# Step 4: Secrets set?
S4=$(gh secret list --repo "$REPO_PATH" 2>/dev/null | grep -c "SNOWFLAKE_ACCOUNT" || echo 0)
# Runner: any local runner online?
RUNNER=$(gh api "repos/$REPO_PATH/actions/runners" --jq '.runners|length' 2>/dev/null || echo 0)
```

⚠️ MANDATORY: call `enter_plan_mode` now. Then present the state summary:

```
Existing repo detected — here's what's already done:

  ✓  Create Project       $REPO_PATH cloned locally
  [$S2 == false → ✓ | else → ✗]  Hold Before Go-Live   Actions enabled: $S2
  [$S3 == done  → ✓ | else → ✗]  Connect Snowflake     OIDC user: $S3
  [$S4 >= 1     → ✓ | else → ✗]  Configure             Secrets set: $S4
  [$RUNNER > 0  → ✓ | else → —]  Runner                Online: $RUNNER
```

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Resume"
  question: "Detected state shown above. Where would you like to start?"
  options:
    - label: "Resume from first incomplete step"
      description: "Skip what's already done and continue from where you left off"
    - label: "Start from the beginning"
      description: "Re-run all steps (idempotent — safe to re-run)"
    - label: "Stop here"
```

If "Resume from first incomplete step":
- If S2 is not `false` → jump to Hold Before Go-Live
- Else if S3 is not `done` → jump to Connect Snowflake
- Else if S4 < 1 → jump to Configure
- Else → jump to Watch the Loop (all setup steps done)

If "Start from the beginning": proceed to Hold Before Go-Live (step 1 already done).



---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Working from a versioned template guarantees every project starts from a
> known-good baseline — OIDC wiring, workflow structure, and prompt files are
> all pre-tested. You own the fork; the template repo is never modified.

**What we'll do**
```
Creates: $REPO_PATH  ($REPO_VISIBILITY, from https://github.com/Snowflake-Labs/github-coco-agent)
Clones:  ./$REPO_NAME
```

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Create Project"
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
  --$REPO_VISIBILITY \
  --clone

# Disable Actions immediately — prevents spurious workflow runs during setup
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT \
  --input - <<'EOF'
{"enabled": false}
EOF
```

**Post-step verification:**
```bash
gh api "repos/$REPO_PATH" --jq .visibility   # confirm remote exists
ls "$REPO_NAME"                               # confirm local clone exists
```
If either check fails:
> ⚠️ **Gate check failed:** Repo creation may not have completed fully.
> Check the output above and retry this step.

### What we did
- Repo created at `$(gh repo view "$REPO_PATH" --json url -q .url)` ($REPO_VISIBILITY)
- Local clone in `./$REPO_NAME`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Create Project done"
  question: "Repo created and cloned. Continue to Hold Before Go-Live?"
  options:
    - label: "Yes, continue"
    - label: "Replay this step"
    - label: "Stop here"
```

---

## Hold Before Go-Live

**Gate check:**
```bash
gh api "repos/$REPO_PATH" --jq .name 2>&1   # remote repo accessible
ls "$REPO_NAME" 2>&1                          # local clone present
```
If either fails:
> ⚠️ **Gate check failed:** Remote repo or local clone not found.
> Complete "Create Project" before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Actions were disabled immediately when the repo was created to prevent
> spurious workflow failures during setup. This step confirms that state
> and ensures you don't accidentally re-enable Actions too early.

**What we'll do**
```
Verifies:  GitHub Actions disabled on $REPO_PATH
Expected:  enabled = false
```

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Hold Before Go-Live"
  question: "Confirm Actions are disabled on $REPO_PATH before proceeding?"
  options:
    - label: "Yes, verify and continue"
    - label: "Stop here"
```

**Verify:**
```bash
gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```
Expected: `false`. If `true`, Actions were re-enabled somehow — re-disable:
```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<'EOF'
{"enabled": false}
EOF
```

### What we did
- Confirmed GitHub Actions are disabled on `$REPO_PATH`
- No workflows will fire until Watch the Loop re-enables them

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Hold Before Go-Live done"
  question: "Actions confirmed disabled. Continue to Connect Snowflake?"
  options:
    - label: "Yes, continue"
    - label: "Stop here"
```

---

## Connect Snowflake

**Gate check:**
```bash
gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```
Expected: `false`. If `true`:
> ⚠️ **Gate check failed:** Actions are still enabled.
> Complete "Hold Before Go-Live" before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> WORKLOAD_IDENTITY replaces long-lived passwords with short-lived OIDC tokens.
> GitHub proves the runner's identity; Snowflake verifies the issuer and subject
> claim. No secret is ever stored — the token exists only for the duration of the job.
>
> The `SNOWFLAKE.CORTEX_USER` database role is also granted — not to access databases,
> but to unlock Cortex AI endpoints. `cortex exec` authenticates via OIDC, then calls
> Snowflake's Cortex REST API. Without this role the session is valid but every
> LLM inference call returns 403 Forbidden.

**What we'll do**

| Object | Value |
|--------|-------|
| Role | `${PREFIX}_GITHUB_COCO_AGENT_ROLE` |
| Warehouse | `${PREFIX}_GITHUB_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `${PREFIX}_GITHUB_COCO_AGENT_USER` |
| Auth | TYPE = WORKLOAD_IDENTITY, OIDC issuer: https://token.actions.githubusercontent.com |
| Subject | `repo:$REPO_PATH:ref:refs/heads/main` |

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Connect Snowflake"
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

**Post-step verification:**
```bash
snow sql -q "DESC USER ${PREFIX}_GITHUB_COCO_AGENT_USER" --format json 2>&1
```
If DESC fails:
> ⚠️ **Gate check failed:** OIDC user not found after provisioning.
> Check the output above and re-run this step.

Also verify role and warehouse exist:
```bash
snow sql -q "SHOW ROLES LIKE '${PREFIX}_GITHUB_COCO_AGENT_ROLE'" --format json 2>&1
snow sql -q "SHOW WAREHOUSES LIKE '${PREFIX}_GITHUB_COCO_AGENT_WH'" --format json 2>&1
```
If either returns empty rows, the setup SQL did not complete — re-run this step.

### What we did
- Role, warehouse, and WORKLOAD_IDENTITY user created and verified
- Subject claim bound to `repo:$REPO_PATH:ref:refs/heads/main`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Connect Snowflake done"
  question: "Snowflake resources ready. Continue to Configure?"
  options:
    - label: "Yes, continue"
    - label: "Replay this step"
    - label: "Stop here"
```

---

## Configure

**Gate check:**
```bash
snow sql -q "DESC USER ${PREFIX}_GITHUB_COCO_AGENT_USER" --format json 2>&1
```
If empty or error:
> ⚠️ **Gate check failed:** OIDC user not found.
> Complete "Connect Snowflake" before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Three config values (account, role, warehouse) tell the workflow which Snowflake
> context to enter. Combined with the OIDC token, this is the complete auth context —
> no password, no API key is ever stored.

**What we'll do**

| Secret | Value |
|--------|-------|
| `SNOWFLAKE_ACCOUNT` | `$SNOWFLAKE_ACCOUNT` |
| `SNOWFLAKE_ROLE` | `${PREFIX}_GITHUB_COCO_AGENT_ROLE` |
| `SNOWFLAKE_WAREHOUSE` | `${PREFIX}_GITHUB_COCO_AGENT_WH` |

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Configure"
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

**Post-step verification:**
```bash
gh secret list --repo "$REPO_PATH" 2>&1
```
Confirm `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE` are listed.

### What we did
- 3 secrets set on `$REPO_PATH`
- Workflows can now authenticate to Snowflake via OIDC

⚠️ MANDATORY pause — local runner:
```
ask_user_question:
  header: "Local runner"
  question: "The workflows run on a self-hosted local runner. Set one up now for testing?"
  options:
    - label: "Yes, install runner inside the repo"
      description: "Installs to .github/runner/ — isolated per project, gitignored, removed with the repo"
    - label: "Skip — use GitHub-hosted runners"
      description: "Set up manually later: Settings → Actions → Runners → New self-hosted runner"
    - label: "Stop here"
```

If "Yes, install runner inside the repo":

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> A project-local runner lets you test the full loop before committing to
> GitHub-hosted runners. It lives inside the repo so it is always discoverable
> and removed cleanly on teardown.

**What we'll do**
```
Installs:   $REPO_NAME/.github/runner/  (gitignored)
Configures: runner bound to https://github.com/$REPO_PATH
Labels:     self-hosted, local
Patches:    runs-on in cortex-scan.yml and cortex-fix.yml → [self-hosted, local]
Note:       binary is ~100 MB — download takes a moment
```

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Install runner"
  question: "Install local runner in $REPO_NAME/.github/runner/?"
  options:
    - label: "Yes, install"
    - label: "Stop here"
```

Execute:
```bash
mkdir -p "$REPO_NAME/.github/runner"
echo '.github/runner/' >> "$REPO_NAME/.gitignore"
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz" \
  | tar xz -C "$REPO_NAME/.github/runner"
RUNNER_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/registration-token" -X POST -q .token)
"$REPO_NAME/.github/runner/config.sh" \
  --url "https://github.com/$REPO_PATH" \
  --token "$RUNNER_TOKEN" \
  --labels "self-hosted,local" \
  --unattended
sed -i '' 's/runs-on: ubuntu-latest/runs-on: [self-hosted, local]/g' \
  "$REPO_NAME/.github/workflows/cortex-scan.yml" \
  "$REPO_NAME/.github/workflows/cortex-fix.yml"
git -C "$REPO_NAME" add .github/workflows/
git -C "$REPO_NAME" commit -m "ci(workflows): use self-hosted local runner for testing [skip ci]"
```

Then ask:
```
ask_user_question:
  header: "Start runner"
  question: "Runner configured. Open a NEW terminal, run the command below, and wait for 'Listening for Jobs':\n\n  $REPO_NAME/.github/runner/run.sh"
  options:
    - label: "Runner is listening — continue"
    - label: "Stop here"
```

**Post-step verification:**
```bash
gh api "repos/$REPO_PATH/actions/runners" \
  --jq '.runners[] | {name, status, labels: [.labels[].name]}'
```
If status is not `online`:
> ⚠️ **Gate check failed:** Runner is not online.
> Check the runner terminal and ensure `run.sh` is still running.

### What we did
- Runner installed in `$REPO_NAME/.github/runner/` and online
- Workflows patched to `runs-on: [self-hosted, local]`

> To restore `ubuntu-latest` later: `git revert HEAD --no-edit && git push`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Configure done"
  question: "Setup complete. Want to test with a sample app?"
  options:
    - label: "Yes, run smoke test and watch the loop"
      description: "Copies a 3-issue Python app into demo/, enables Actions, commits and pushes"
    - label: "No, I'll push my own code later"
      description: "Actions stay disabled — re-enable with: gh api repos/$REPO_PATH/actions/permissions -X PUT --input - <<<'{\"enabled\":true}'"
    - label: "Stop here"
```

---

## Watch the Loop (optional)

Only execute if user chose "Yes, run smoke test" in Configure.

**Gate check (if local runner was set up):**
```bash
gh api "repos/$REPO_PATH/actions/runners" --jq '.runners | length'
```
If 0:
> ⚠️ **Gate check failed:** No runner is online.
> Start `.github/runner/run.sh` in a new terminal before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> The smoke-test app contains 3 intentional security and correctness issues.
> Running it proves the loop end-to-end: scan finds issues, fix agents patch
> them, PRs are opened automatically. No production code is touched.

**What we'll do**
```
Step 1: write smoke-test app (3 files) to $REPO_NAME/demo/
Step 2: enable Actions on $REPO_PATH
Step 3: commit + push  (revertable — git revert HEAD when done)
Step 4: show Actions URL
```

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Watch the Loop"
  question: "Copy smoke-test app, enable Actions, and push to trigger the loop?"
  options:
    - label: "Yes, run the smoke test"
    - label: "Stop here"
```

**Step 1 — Copy templates:**
Read `skills/scaffold/references/smoke-test.md` and write the files from
`skills/scaffold/templates/smoke-test/` to `$REPO_NAME/demo/`.

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
git commit -m "test(smoke): add intentional-issue app for CI/CD loop validation"
git push
```

⚠️ This is a revertable test commit. Clean up when done:
```bash
git revert HEAD --no-edit && git push
```

**Step 4 — Show Actions URL:**
```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
```

### What we did
- Smoke-test app pushed to `demo/`
- Actions enabled — scan workflow will trigger on the runner
- Issues and PRs will appear automatically

See `skills/scaffold/references/smoke-test.md` for expected output.
For local testing without a live Actions runner, see `skills/scaffold/references/local-testing.md`.

⚠️ MANDATORY pause (repeatable until satisfied):
```
ask_user_question:
  header: "Watch the Loop"
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

## Clean Up (optional)

```
ask_user_question:
  header: "Clean Up"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources and delete the GitHub repo"
    - label: "Drop Snowflake only"
    - label: "Keep everything"
```

If "Keep everything" → stop.

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Resources left running after a demo cost credits. Teardown reverses the setup
> in order: deregister runner → drop Snowflake objects → delete repo.
> Skipping any step leaves orphaned objects.

**What we'll drop**
```
[if "tear down everything"]
  Runner:    deregistered from $REPO_PATH (if installed)
  Snowflake: ${PREFIX}_GITHUB_COCO_AGENT_ROLE / _WH / _USER dropped
  Repo:      $REPO_PATH deleted from GitHub

[if "Drop Snowflake only"]
  Snowflake: ${PREFIX}_GITHUB_COCO_AGENT_ROLE / _WH / _USER dropped
  Runner and repo: kept
```

Call `exit_plan_mode`. Then ask (always fires regardless of mode — destructive and irreversible):
```
ask_user_question:
  header: "Confirm teardown"
  question: "⚠️ This is irreversible. Proceed with teardown?"
  options:
    - label: "Yes, tear down now"
    - label: "Abort"
```

Execute:
```bash
# Deregister local runner (if installed)
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
  sed -i '' 's/runs-on: \[self-hosted, local\]/runs-on: ubuntu-latest/g' \
    "$REPO_NAME/.github/workflows/cortex-scan.yml" \
    "$REPO_NAME/.github/workflows/cortex-fix.yml"
  git -C "$REPO_NAME" add .github/workflows/
  git -C "$REPO_NAME" commit -m "ci(workflows): restore ubuntu-latest runner [skip ci]" 2>/dev/null || true
fi

snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"
gh repo delete "$REPO_PATH" --yes
```

### What we did
- Runner deregistered (if installed)
- Snowflake objects dropped
- Repo deleted

> ✓ **Done:** Environment is clean.
