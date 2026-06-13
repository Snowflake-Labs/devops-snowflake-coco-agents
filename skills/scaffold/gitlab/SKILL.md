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

## Run Mode and Project Name

Read `skills/scaffold/references/run-mode.md` and follow Steps A and B before
collecting any other inputs. Set `$SKILL_MODE` and prepare the project name
`defaultValue` from the petname output before proceeding to Stopping Points.

## Stopping Points

Collect all four values before Beat 1.

1. **Target project** (`PROJECT_PATH`) — detect GitLab username:
   ```bash
   glab api user --field username
   ```
   Use the petname generated in Step B of `run-mode.md` as the `defaultValue`:
   ```
   ask_user_question:
     header: "New project"
     question: "Full path for the new project? (generated suggestion — edit freely)"
     type: text
     defaultValue: "<detected-username>/<generated-petname>"
   ```

2. **Snowflake prefix** (`PREFIX`) — ask:
   ```
   ask_user_question:
     header: "Prefix"
     question: "Snowflake resource prefix? All objects will be named PREFIX_GITLAB_COCO_AGENT_*"
     type: text
     defaultValue: "DEMO"
   ```

3. **Snowflake account** (`SNOWFLAKE_ACCOUNT`) — check `$SNOWFLAKE_ACCOUNT` env first; if unset, ask.

4. **GitLab bot token** (`GITLAB_TOKEN_coco`) — ask:
   ```
   ask_user_question:
     header: "GitLab token"
     question: "GitLab PAT for the bot service account (needs api + write_repository scope). Stored as masked CI/CD variable."
     type: text
     defaultValue: ""
   ```

Derive group, project name, and encoded path for later:
```bash
GROUP="${PROJECT_PATH%/*}"
PROJECT_NAME="${PROJECT_PATH##*/}"
ENCODED_PATH=$(python3 -c "import urllib.parse,os; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")
```

---

## Beat 1 — Scaffold project from template

Enter plan mode and present:

**Why this matters** (Guided mode only):
Working from a versioned template guarantees every project starts from a known-good
baseline — OIDC wiring, pipeline structure, and prompt files are all pre-tested.
You own the fork; the template project is never modified.

**What we'll do:**
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
  question: "Project created and cloned. Continue to Beat 2 (disable pipelines)?"
  options:
    - label: "Yes, continue to Beat 2"
    - label: "Replay Beat 1"
    - label: "Stop here"
```

---

## Beat 2 — Repo Init (disable pipelines)

Enter plan mode and present:

**Why this matters** (Guided mode only):
Running pipelines before auth is configured produces failed OIDC exchanges and
confusing error messages. Disabling now means the first real run will be a clean
green one.

**What we'll do:**
```
Disables:  CI/CD pipelines on $PROJECT_PATH
Effect:    No jobs fire until Beat 5 re-enables them
Command:   glab api projects/$ENCODED_PATH -X PUT -F builds_access_level=disabled
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 2"
  question: "Disable CI/CD pipelines on $PROJECT_PATH until setup is complete?"
  options:
    - label: "Yes, disable pipelines"
    - label: "Replay Beat 2"
    - label: "Stop here"
```

Execute:
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

Enter plan mode and present:

**Why this matters** (Guided mode only):
WORKLOAD_IDENTITY replaces long-lived passwords with short-lived OIDC tokens.
GitLab proves the runner's identity; Snowflake verifies the issuer and subject
claim. No secret is ever stored — the token exists only for the duration of the job.

**What we'll do:**
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

Enter plan mode and present:

**Why this matters** (Guided mode only):
Four config values tell the pipeline which Snowflake context to enter and how to
authenticate with GitLab as the bot account. Combined with the OIDC token from
Beat 3, no long-lived Snowflake credential is needed.

**What we'll do:**
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

⚠️ MANDATORY pause — local runner:
```
ask_user_question:
  header: "Local runner"
  question: "Pipelines run on GitLab shared runners by default. Set up a project-local runner now for testing?"
  options:
    - label: "Yes, install runner inside the repo"
      description: "Installs gitlab-runner to .gitlab/runner/ — shell executor, isolated per project, gitignored"
    - label: "Skip — use GitLab shared runners"
      description: "Re-enable pipelines with: glab api projects/$ENCODED_PATH -X PUT -F builds_access_level=enabled"
    - label: "Stop here"
```

If "Yes, install runner inside the repo":

Enter plan mode and present:

**Why this matters** (Guided mode only):
A project-local registered runner lets you test the full loop without waiting for
a shared runner slot. The shell executor uses the cortex binary on PATH directly —
no Docker image build needed. It lives inside the repo so it is always discoverable
and removed cleanly on teardown.

**What we'll do:**
```
Downloads:   $PROJECT_NAME/.gitlab/runner/  (gitignored)
Executor:    shell (uses cortex from PATH — no Docker required)
Tag:         local (only jobs with tags: [local] will run on this runner)
Patches:     tags: [local] added to scan-code and coco-agent in .gitlab-ci.yml
Note:        binary is ~80 MB — download takes a moment
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Install runner"
  question: "Install local GitLab runner in $PROJECT_NAME/.gitlab/runner/?"
  options:
    - label: "Yes, install"
    - label: "Stop here"
```

Execute:
```bash
# 1. Download runner binary
mkdir -p "$PROJECT_NAME/.gitlab/runner"
echo '.gitlab/runner/' >> "$PROJECT_NAME/.gitignore"
RUNNER_VERSION=$(curl -s \
  "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab-runner/releases/permalink/latest" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
curl -LsS \
  "https://gitlab-runner-downloads.s3.amazonaws.com/v${RUNNER_VERSION}/binaries/gitlab-runner-darwin-arm64" \
  -o "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
chmod +x "$PROJECT_NAME/.gitlab/runner/gitlab-runner"

# 2. Create runner token via GitLab API (requires glab auth)
PROJECT_ID=$(glab api "projects/$ENCODED_PATH" --jq .id)
RUNNER_TOKEN=$(glab api "user/runners" -X POST \
  --field "runner_type=project_type" \
  --field "project_id=$PROJECT_ID" \
  --field "tag_list=local" \
  --field "run_untagged=false" \
  --field "description=local-mac" \
  --jq .token)

# 3. Register with project-local config
"$PROJECT_NAME/.gitlab/runner/gitlab-runner" register \
  --config "$PROJECT_NAME/.gitlab/runner/config.toml" \
  --url https://gitlab.com \
  --token "$RUNNER_TOKEN" \
  --executor shell \
  --non-interactive

# 4. Patch pipeline jobs to use local tag
python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)", rf"\1\n  tags: [local]", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Patched .gitlab-ci.yml: tags: [local] added to scan-code and coco-agent")
PYEOF
git -C "$PROJECT_NAME" add .gitlab-ci.yml .gitignore
git -C "$PROJECT_NAME" commit -m "ci: use self-hosted local runner for testing [skip ci]"

# 5. Capture runner ID for teardown
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

Verify runner is online:
```bash
glab api "projects/$ENCODED_PATH/runners" \
  --jq '.[] | select(.description == "local-mac") | {id, status, tag_list}'
```
If status is not `online`, ask the user to check the runner terminal before proceeding.

**What we did:**
Runner installed in `$PROJECT_NAME/.gitlab/runner/`, pipeline patched to add
`tags: [local]` on `scan-code` and `coco-agent`, committed.
Runner ID is `$RUNNER_ID` — keep it for teardown.

> To restore default runner later: `git revert HEAD --no-edit && git push`

⚠️ MANDATORY pause:
```
ask_user_question:
  header: "Beat 4 done"
  question: "Variables set and runner ready. Want to test with a sample app?"
  options:
    - label: "Yes, run smoke test and watch the loop"
      description: "Copies a 3-issue Python app into demo/ (CI-watched folder), enables pipelines, commits as revertable test commit and pushes"
    - label: "No, I'll push my own code later"
      description: "Re-enable pipelines with: glab api projects/$ENCODED_PATH -X PUT -F builds_access_level=enabled"
    - label: "Stop here"
```

---

## Beat 5 — Smoke test (optional)

Only execute if user chose "Yes, run smoke test" in Beat 4.

Enter plan mode and present:

**Why this matters** (Guided mode only):
The smoke-test app contains 3 intentional security and correctness issues. Running
it proves the loop end-to-end: scan finds issues, CoCo fixes them, MRs are opened
automatically. No production code is touched — this is a safe, revertable test.

**What we'll do:**
```
Step 1: write smoke-test app (3 files) to $PROJECT_NAME/demo/
Step 2: enable pipelines on $PROJECT_PATH
Step 3: commit + push  (revertable — git revert HEAD when done)
Step 4: trigger pipeline + show URL
```

Exit plan mode, then ask:
```
ask_user_question:
  header: "Beat 5"
  question: "Copy smoke-test app, enable pipelines, and push to trigger the loop?"
  options:
    - label: "Yes, run the smoke test"
    - label: "Stop here"
```

**Step 1 — Copy templates:**
Read `skills/scaffold/references/smoke-test.md` for the full template description
and copy instructions, then write the files from `skills/scaffold/templates/smoke-test/`
to `$PROJECT_NAME/demo/`.

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

⚠️ This is a revertable test commit. Once the loop has validated, clean up with:
```bash
git revert HEAD --no-edit && git push
```

**Step 4 — Trigger pipeline and show URL:**
```bash
glab pipeline run --branch main
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
```

**What we did:**
Smoke-test app pushed to `demo/`. Pipelines enabled. The scan-code job will trigger
on the runner and create `[coco-agent]` issues; each issue triggers the coco-agent job.
See `skills/scaffold/references/smoke-test.md` for what to expect.
For local testing options, see `skills/scaffold/references/local-testing.md`.

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

If "Keep everything" → stop.

Enter plan mode and present:

**Why this matters** (Guided mode only):
Resources left running after a demo cost credits. Teardown reverses Beats 3–4 in
order: deregister runner → drop Snowflake objects → delete project. Skipping any
step leaves orphaned objects.

**What we'll drop:**
```
[if "tear down everything"]
  Runner:    deregistered from $PROJECT_PATH (if installed, ID: $RUNNER_ID)
  Snowflake: ${PREFIX}_GITLAB_COCO_AGENT_ROLE / _WH / _USER dropped
  Project:   $PROJECT_PATH deleted from GitLab

[if "Drop Snowflake only"]
  Snowflake: ${PREFIX}_GITLAB_COCO_AGENT_ROLE / _WH / _USER dropped
  Runner and project: kept
```

Exit plan mode, then ask (always fires regardless of mode — destructive and irreversible):
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
  # Revert pipeline tag patch
  python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)\n  tags: \[local\]", rf"\1", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Reverted .gitlab-ci.yml: tags: [local] removed")
PYEOF
  git -C "$PROJECT_NAME" add .gitlab-ci.yml
  git -C "$PROJECT_NAME" commit -m "ci: restore default runner [skip ci]" 2>/dev/null || true
fi

snow sql -f "$PROJECT_NAME/snowflake/teardown.sql" \
  -D "PREFIX=$PREFIX" \
  --enable-templating STANDARD

glab project delete "$PROJECT_PATH" --yes
```

**What we did:**
Runner deregistered. Snowflake objects dropped. Project deleted. Environment is clean.
