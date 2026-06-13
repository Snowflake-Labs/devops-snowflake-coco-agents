---
name: scaffold-for-gitlab
description: >
  Guided 6-step scaffold: set up a new GitLab CI CoCo agent project from
  the gitlab-coco-agent template. Provisions Snowflake OIDC resources, sets
  GitLab CI/CD variables, and optionally pushes a sample app to trigger the
  scan->issue->fix automation loop end-to-end.
  Use when the user chose the GitLab path, or invoked
  $devops-coco-agents:scaffold-for-gitlab directly.
---

## Plan Mode Rule

⚠️ MANDATORY on every step: call `enter_plan_mode` **before** presenting any
content (Why this matters, What we'll do, resource tables, command previews).
Call `exit_plan_mode` immediately after the preview — the plan mode confirmation
IS the single execute gate. After `exit_plan_mode`, execute directly without
asking again. Only steps with genuine branching options (e.g. "Show setup.sql
first") keep a post-exit question.

## Step Order

⚠️ MANDATORY: Execute steps 1–6 in order. Never skip or reorder.
Each step builds on the previous — jumping ahead leaves the project in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template project (`https://gitlab.com/kameshsampath/gitlab-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set CI/CD variables other than the four listed in Configure.
- Do not enable pipelines before Configure is complete.

## Prerequisites Check

Run both checks before collecting any inputs. If either fails, stop and help
the user fix it before proceeding.

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

**Multi-account detection:**
Parse the current username from `glab auth status 2>&1` by extracting
`"Logged in to gitlab.com as <username>"`.

Always confirm the active account:
```
ask_user_question:
  header: "GitLab account"
  question: "Currently logged into GitLab as <detected-username>. Use this account?"
  options:
    - label: "Yes, use <detected-username>"
    - label: "Switch to a different account"
      description: "Logs out the current account — you will re-authenticate with the new one"
```

If "Switch to a different account":
```
ask_user_question:
  header: "Switch account"
  question: "Run these commands in your terminal, then come back:\n\n  glab auth logout --hostname gitlab.com\n  glab auth login --hostname gitlab.com"
  options:
    - label: "Done, I've switched"
    - label: "Cancel, keep current account"
```
If "Done": re-run `glab auth status 2>&1`, confirm new username.

> ✓ **Done:** Using GitLab account `<confirmed-username>`.

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

Read `skills/scaffold/references/run-mode.md` and follow Steps A–D before
collecting any other inputs:
- Step A sets `$SKILL_MODE`
- Step B generates the petname for the project name `defaultValue`
- Step C detects Snowflake username → `$PREFIX`
- Step D detects or asks for `$SNOWFLAKE_ACCOUNT`

Also read `skills/scaffold/references/output-format.md` (formatting rules).

## Stopping Points

Collect all four values before Create Project.

1. **Target project** (`PROJECT_PATH`) — detect GitLab username:
   ```bash
   glab api user --field username
   ```
   Use the petname from Step B of `run-mode.md` as the `defaultValue`.
   Track the generated name as `GENERATED_PETNAME` for conflict detection.

   ```
   ask_user_question:
     header: "New project"
     question: "Full path for the new project? (generated suggestion — edit freely)"
     type: text
     defaultValue: "<detected-username>/<generated-petname>"
   ```

   After the user answers, compare the submitted value to `<detected-username>/<GENERATED_PETNAME>`.
   If they match: `USING_GENERATED = true`. If different: `USING_GENERATED = false`.

2. **Visibility** (`PROJECT_VISIBILITY`) — GitLab supports all three levels.
   Note: `glab project create` defaults to `--internal` if no flag is passed — always
   pass the flag explicitly.

   ```
   ask_user_question:
     header: "Visibility"
     question: "Project visibility? (private is recommended)"
     defaultAnswer: "Private"
     options:
       - label: "Private"
         description: "Only project members can access it"
       - label: "Internal"
         description: "Visible to any authenticated GitLab user"
       - label: "Public"
         description: "Visible without authentication"
   ```

   Flag mapping: Private → `--private`, Internal → `--internal`, Public → `--public`.

3. Use the petname from Step B of `run-mode.md` as the `defaultValue`.
   Track the generated name as `GENERATED_PETNAME` for conflict detection.

5. **GitLab bot token** (`GITLAB_TOKEN_coco`) — ask:
   ```
   ask_user_question:
     header: "GitLab token"
     question: "GitLab PAT for the bot service account (needs api + write_repository scope)."
     type: text
     defaultValue: ""
   ```

Derive group, project name, and encoded path:
```bash
GROUP="${PROJECT_PATH%/*}"
PROJECT_NAME="${PROJECT_PATH##*/}"
ENCODED_PATH=$(python3 -c "import urllib.parse,os; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")
```

---

## Create Project

**Pre-step guard — check remote does not already exist:**
```bash
glab api "projects/$ENCODED_PATH" 2>&1
```

If the project EXISTS and `USING_GENERATED = true`:
- Generate a new petname (see `output-format.md` rotation rules)
- > ℹ️ **Note:** `$PROJECT_PATH` is already taken — here's a fresh suggestion.
- Re-present the name question with new `defaultValue`
- Repeat up to 3 times; after 3 failures set `USING_GENERATED = false` and ask user to type their own

If the project EXISTS and `USING_GENERATED = false`:
```
ask_user_question:
  header: "Project exists"
  question: "`$PROJECT_PATH` already exists on GitLab. What would you like to do?"
  options:
    - label: "Use the existing project"
      description: "Skip creation, clone it, and proceed to Hold Before Go-Live"
    - label: "Choose a different path"
      description: "Pick a new path and retry this step"
    - label: "Abort"
```

If "Use the existing project":
```bash
glab repo clone "$PROJECT_PATH"
```

Then run state detection to find where to resume:
```bash
echo "=== Detecting completed steps ==="
# Step 2: Pipelines state
S2=$(glab api "projects/$ENCODED_PATH" --jq .builds_access_level 2>/dev/null)
# Step 3: OIDC user exists?
S3=$(snow sql -q "SHOW USERS LIKE '${PREFIX}_GITLAB_COCO_AGENT_USER'" \
       --format json 2>/dev/null \
       | python3 -c "import sys,json; print('done' if json.load(sys.stdin) else '')" 2>/dev/null)
# Step 4: CI/CD variables set?
S4=$(glab variable list 2>/dev/null | grep -c "SNOWFLAKE_ACCOUNT" || echo 0)
# Runner: any local runner online?
RUNNER=$(glab api "projects/$ENCODED_PATH/runners" \
           --jq '[.[]|select(.description=="local-mac")]|length' 2>/dev/null || echo 0)
```

⚠️ MANDATORY: call `enter_plan_mode` now. Then present the state summary:

```
Existing project detected — here's what's already done:

  ✓  Create Project       $PROJECT_PATH cloned locally
  [$S2 == disabled → ✓ | else → ✗]  Hold Before Go-Live  Pipelines: $S2
  [$S3 == done     → ✓ | else → ✗]  Connect Snowflake    OIDC user: $S3
  [$S4 >= 1        → ✓ | else → ✗]  Configure            Variables set: $S4
  [$RUNNER > 0     → ✓ | else → —]  Runner               Online: $RUNNER
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
- If S2 is not `disabled` → jump to Hold Before Go-Live
- Else if S3 is not `done` → jump to Connect Snowflake
- Else if S4 < 1 → jump to Configure
- Else → jump to Watch the Loop (all setup steps done)

If "Start from the beginning": proceed to Hold Before Go-Live (step 1 already done).



---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Working from a versioned template guarantees every project starts from a
> known-good baseline — OIDC wiring, pipeline structure, and prompt files are
> all pre-tested. You own the fork; the template project is never modified.

**What we'll do**
```
Creates: $PROJECT_PATH  ($PROJECT_VISIBILITY, from https://gitlab.com/kameshsampath/gitlab-coco-agent)
Clones:  ./$PROJECT_NAME
```

Call `exit_plan_mode`. Then ask:
```
ask_user_question:
  header: "Create Project"
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
  --template-project https://gitlab.com/kameshsampath/gitlab-coco-agent \
  --$PROJECT_VISIBILITY

glab repo clone "$PROJECT_PATH"

# Disable pipelines immediately — prevents spurious runs during setup
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
```

**Post-step verification:**
```bash
glab api "projects/$ENCODED_PATH" --jq .visibility   # confirm remote exists
ls "$PROJECT_NAME"                                     # confirm local clone exists
```
If either check fails:
> ⚠️ **Gate check failed:** Project creation may not have completed fully.
> Check the output above and retry this step.

### What we did
- Project created at `https://gitlab.com/$PROJECT_PATH` ($PROJECT_VISIBILITY)
- Local clone in `./$PROJECT_NAME`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Create Project done"
  question: "Project created and cloned. Continue to Hold Before Go-Live?"
  options:
    - label: "Yes, continue"
    - label: "Replay this step"
    - label: "Stop here"
```

---

## Hold Before Go-Live

**Gate check:**
```bash
glab api "projects/$ENCODED_PATH" --jq .name 2>&1   # remote accessible
ls "$PROJECT_NAME" 2>&1                               # local clone present
```
If either fails:
> ⚠️ **Gate check failed:** Remote project or local clone not found.
> Complete "Create Project" before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Pipelines were disabled immediately when the project was created to prevent
> spurious pipeline failures during setup. This step confirms that state
> and ensures you don't accidentally re-enable pipelines too early.

**What we'll do**
```
Verifies:  CI/CD pipelines disabled on $PROJECT_PATH
Expected:  builds_access_level = "disabled"
```

Call `exit_plan_mode`. Then execute directly:

**Verify:**
```bash
glab api "projects/$ENCODED_PATH" --jq .builds_access_level
```
Expected: `"disabled"`. If not, re-disable:
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
```

### What we did
- Confirmed CI/CD pipelines are disabled on `$PROJECT_PATH`
- No jobs will fire until Watch the Loop re-enables them

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Hold Before Go-Live done"
  question: "Pipelines confirmed disabled. Continue to Connect Snowflake?"
  options:
    - label: "Yes, continue"
    - label: "Stop here"
```

---

## Connect Snowflake

**Gate check:**
```bash
glab api "projects/$ENCODED_PATH" --jq .builds_access_level
```
Expected: `"disabled"`. If not:
> ⚠️ **Gate check failed:** Pipelines are still enabled.
> Complete "Hold Before Go-Live" before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> WORKLOAD_IDENTITY replaces long-lived passwords with short-lived OIDC tokens.
> GitLab proves the runner's identity; Snowflake verifies the issuer and subject
> claim. No secret is ever stored — the token exists only for the duration of the job.
>
> The `SNOWFLAKE.CORTEX_USER` database role is also granted — not to access databases,
> but to unlock Cortex AI endpoints. `cortex exec` authenticates via OIDC, then calls
> Snowflake's Cortex REST API. Without this role the session is valid but every
> LLM inference call returns 403 Forbidden.

**What we'll do**

| Object | Value |
|--------|-------|
| Role | `${PREFIX}_GITLAB_COCO_AGENT_ROLE` |
| Warehouse | `${PREFIX}_GITLAB_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `${PREFIX}_GITLAB_COCO_AGENT_USER` |
| Auth | `TYPE = SERVICE`, `WORKLOAD_IDENTITY = (TYPE = OIDC ISSUER = https://gitlab.com)` |
| Subject | `project_path:$PROJECT_PATH:ref_type:branch:ref:main` |

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

If "Show setup.sql first": read and display `$PROJECT_NAME/snowflake/setup.sql`, then re-ask.

Execute:
```bash
snow sql -f "$PROJECT_NAME/snowflake/setup.sql" \
  -D "PREFIX=$PREFIX" \
  -D "REPO_PATH=$PROJECT_PATH" \
  --enable-templating STANDARD
```

**Post-step verification:**
```bash
snow sql -q "DESC USER ${PREFIX}_GITLAB_COCO_AGENT_USER" --format json 2>&1
```
If DESC fails:
> ⚠️ **Gate check failed:** OIDC user not found after provisioning.
> Check the output above and re-run this step.

Also verify role and warehouse exist:
```bash
snow sql -q "SHOW ROLES LIKE '${PREFIX}_GITLAB_COCO_AGENT_ROLE'" --format json 2>&1
snow sql -q "SHOW WAREHOUSES LIKE '${PREFIX}_GITLAB_COCO_AGENT_WH'" --format json 2>&1
```
If either returns empty rows, the setup SQL did not complete — re-run this step.

### What we did
- Role, warehouse, and `SERVICE` user with `WORKLOAD_IDENTITY` OIDC config created and verified
- Subject claim bound to `project_path:$PROJECT_PATH:ref_type:branch:ref:main`

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
snow sql -q "DESC USER ${PREFIX}_GITLAB_COCO_AGENT_USER" --format json 2>&1
```
If empty or error:
> ⚠️ **Gate check failed:** OIDC user not found.
> Complete "Connect Snowflake" before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Four config values tell the pipeline which Snowflake context to enter and how
> to authenticate with GitLab as the bot account. Combined with the OIDC token,
> no long-lived Snowflake credential is needed.

**What we'll do**

| Variable | Value | Masked |
|----------|-------|--------|
| `SNOWFLAKE_ACCOUNT` | `$SNOWFLAKE_ACCOUNT` | yes |
| `SNOWFLAKE_USER` | `${PREFIX}_GITLAB_COCO_AGENT_USER` | no |
| `SNOWFLAKE_WAREHOUSE` | `${PREFIX}_GITLAB_COCO_AGENT_WH` | no |
| `GITLAB_TOKEN_coco` | (provided token) | yes |

Call `exit_plan_mode`. Then execute directly:

```bash
cd "$PROJECT_NAME"
glab variable set SNOWFLAKE_ACCOUNT   --value "$SNOWFLAKE_ACCOUNT"   --masked
glab variable set SNOWFLAKE_USER      --value "${PREFIX}_GITLAB_COCO_AGENT_USER"
glab variable set SNOWFLAKE_WAREHOUSE --value "${PREFIX}_GITLAB_COCO_AGENT_WH"
glab variable set GITLAB_TOKEN_coco   --value "$GITLAB_TOKEN_coco"   --masked
```

**Post-step verification:**
```bash
glab variable list 2>&1
```
Confirm `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_WAREHOUSE`, `GITLAB_TOKEN_coco` are listed.

### What we did
- 4 CI/CD variables set on `$PROJECT_PATH`
- Pipelines can now authenticate to Snowflake via OIDC

⚠️ MANDATORY pause — local runner:
```
ask_user_question:
  header: "Local runner"
  question: "Pipelines run on GitLab shared runners by default. Set up a project-local runner now for testing?"
  options:
    - label: "Yes, install runner inside the repo"
      description: "Installs gitlab-runner to .gitlab/runner/ — shell executor, gitignored"
    - label: "Skip — use GitLab shared runners"
    - label: "Stop here"
```

If "Yes, install runner inside the repo":

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> A project-local registered runner lets you test the full loop without waiting
> for a shared runner slot. The shell executor uses the cortex binary on PATH
> directly — no Docker image build needed.

**What we'll do**
```
Downloads:   $PROJECT_NAME/.gitlab/runner/  (gitignored)
Executor:    shell (uses cortex from PATH — no Docker required)
Tag:         local
Patches:     tags: [local] added to scan-code and coco-agent in .gitlab-ci.yml
```

Call `exit_plan_mode`. Then execute directly:

```bash
mkdir -p "$PROJECT_NAME/.gitlab/runner"
echo '.gitlab/runner/' >> "$PROJECT_NAME/.gitignore"
RUNNER_VERSION=$(curl -s \
  "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab-runner/releases/permalink/latest" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://gitlab-runner-downloads.s3.amazonaws.com/v${RUNNER_VERSION}/binaries/gitlab-runner-darwin-arm64" \
  -o "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
chmod +x "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
PROJECT_ID=$(glab api "projects/$ENCODED_PATH" --jq .id)
RUNNER_TOKEN=$(glab api "user/runners" -X POST \
  --field "runner_type=project_type" \
  --field "project_id=$PROJECT_ID" \
  --field "tag_list=local" \
  --field "run_untagged=false" \
  --field "description=local-mac" \
  --jq .token)
"$PROJECT_NAME/.gitlab/runner/gitlab-runner" register \
  --config "$PROJECT_NAME/.gitlab/runner/config.toml" \
  --url https://gitlab.com \
  --token "$RUNNER_TOKEN" \
  --executor shell \
  --non-interactive
python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)", rf"\1\n  tags: [local]", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Patched: tags: [local] added to scan-code and coco-agent")
PYEOF
git -C "$PROJECT_NAME" add .gitlab-ci.yml .gitignore
git -C "$PROJECT_NAME" commit -m "ci: use self-hosted local runner for testing [skip ci]"
RUNNER_ID=$(glab api "projects/$ENCODED_PATH/runners" \
  --jq '.[] | select(.description == "local-mac") | .id' | head -1)
echo "Runner ID: $RUNNER_ID  (keep this — needed for teardown)"
```

Then ask:
```
ask_user_question:
  header: "Start runner"
  question: "Runner configured. Open a NEW terminal, run the command below, and wait for 'Listening for Jobs':\n\n  $PROJECT_NAME/.gitlab/runner/gitlab-runner run --config $PROJECT_NAME/.gitlab/runner/config.toml"
  options:
    - label: "Runner is listening — continue"
    - label: "Stop here"
```

**Post-step verification:**
```bash
glab api "projects/$ENCODED_PATH/runners" \
  --jq '.[] | select(.description == "local-mac") | {id, status, tag_list}'
```
If status is not `online`:
> ⚠️ **Gate check failed:** Runner is not online.
> Check the runner terminal and ensure the `gitlab-runner run` command is still running.

### What we did
- Runner installed in `$PROJECT_NAME/.gitlab/runner/` and online
- Runner ID: `$RUNNER_ID` (save for teardown)
- Pipeline patched to add `tags: [local]` on `scan-code` and `coco-agent`

> To restore default runner later: `git revert HEAD --no-edit && git push`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Configure done"
  question: "Setup complete. Want to test with a sample app?"
  options:
    - label: "Yes, run smoke test and watch the loop"
      description: "Copies a 3-issue Python app into demo/, enables pipelines, commits and pushes"
    - label: "No, I'll push my own code later"
      description: "Re-enable pipelines with: glab api projects/$ENCODED_PATH -X PUT -F builds_access_level=enabled"
    - label: "Stop here"
```

---

## Watch the Loop (optional)

Only execute if user chose "Yes, run smoke test" in Configure.

**Gate check (if local runner was set up):**
```bash
glab api "projects/$ENCODED_PATH/runners" \
  --jq '[.[] | select(.description == "local-mac")] | length'
```
If 0:
> ⚠️ **Gate check failed:** No runner is online.
> Start `.gitlab/runner/gitlab-runner run` in a new terminal before continuing.

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> The smoke-test app contains 3 intentional security and correctness issues.
> Running it proves the loop end-to-end: scan finds issues, CoCo fixes them,
> MRs are opened automatically. No production code is touched.

**What we'll do**
```
Step 1: write smoke-test app (3 files) to $PROJECT_NAME/demo/
Step 2: enable pipelines on $PROJECT_PATH
Step 3: commit + push  (revertable — git revert HEAD when done)
Step 4: trigger pipeline + show URL
```

Call `exit_plan_mode`. Then execute directly:

**Step 1 — Copy templates:**
Read `skills/scaffold/references/smoke-test.md` and write the files from
`skills/scaffold/templates/smoke-test/` to `$PROJECT_NAME/demo/`.

**Step 2 — Enable pipelines:**
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=enabled 2>&1
```

**Step 3 — Commit and push:**
```bash
cd "$PROJECT_NAME"
git add demo/
git commit -m "test(smoke): add intentional-issue app for CI/CD loop validation"
git push
```

⚠️ Revertable test commit. Clean up when done:
```bash
git revert HEAD --no-edit && git push
```

**Step 4 — Trigger pipeline and show URL:**
```bash
glab pipeline run --branch main
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
```

### What we did
- Smoke-test app pushed to `demo/`
- Pipelines enabled — `scan-code` job will trigger on the runner
- Issues and MRs will appear automatically

See `skills/scaffold/references/smoke-test.md` for expected output.
For local testing options, see `skills/scaffold/references/local-testing.md`.

⚠️ MANDATORY pause (repeatable until satisfied):
```
ask_user_question:
  header: "Watch the Loop"
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

## Clean Up (optional)

```
ask_user_question:
  header: "Clean Up"
  question: "Tear down the project resources?"
  options:
    - label: "Yes, tear down everything"
      description: "Drop Snowflake resources and delete the GitLab project"
    - label: "Drop Snowflake only"
    - label: "Keep everything"
```

If "Keep everything" → stop.

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Resources left running after a demo cost credits. Teardown reverses the setup
> in order: deregister runner → drop Snowflake objects → delete project.
> Skipping any step leaves orphaned objects.

**What we'll drop**
```
[if "tear down everything"]
  Runner:    deregistered from $PROJECT_PATH (if installed, ID: $RUNNER_ID)
  Snowflake: ${PREFIX}_GITLAB_COCO_AGENT_ROLE / _WH / _USER dropped
  Project:   $PROJECT_PATH deleted from GitLab

[if "Drop Snowflake only"]
  Snowflake: ${PREFIX}_GITLAB_COCO_AGENT_ROLE / _WH / _USER dropped
  Runner and project: kept
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
if [ -n "$RUNNER_ID" ]; then
  glab api "projects/$ENCODED_PATH/runners/$RUNNER_ID" -X DELETE
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
  git -C "$PROJECT_NAME" commit -m "ci: restore default runner [skip ci]" 2>/dev/null || true
fi

snow sql -f "$PROJECT_NAME/snowflake/teardown.sql" \
  -D "PREFIX=$PREFIX" \
  --enable-templating STANDARD

glab project delete "$PROJECT_PATH" --yes
```

### What we did
- Runner deregistered (if installed)
- Snowflake objects dropped
- Project deleted

> ✓ **Done:** Environment is clean.
