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
Call `exit_plan_mode` immediately after the preview — the plan mode confirmation
IS the single execute gate. After `exit_plan_mode`, execute directly.
Template previews and setup SQL are shown inside plan mode by default.

## Step Order

⚠️ MANDATORY: Execute steps 1–6 in order. Never skip or reorder.
Each step builds on the previous — jumping ahead leaves the repo in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template repo (`https://github.com/Snowflake-Labs/github-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set GitHub secrets other than the three listed in Configure.
- Do not enable Actions before Configure is complete.
- **NEVER modify the local runner's environment** — no `uv tool uninstall`, no `pip uninstall`, no `brew uninstall`, no overwriting `~/.snowflake/connections.toml`. Local runners use what is already installed. The `if: runner.environment == 'github-hosted'` guard in the workflow templates enforces this: snow install and connections.toml write are skipped entirely on self-hosted runners.

## Sensitive Values

⚠️ NEVER echo real values for these variables — use the variable name or placeholder:

| Variable | Mask as | Notes |
|----------|---------|-------|
| `SNOWFLAKE_ACCOUNT` | `<account>` | Show in plan previews as placeholder only |
| `RUNNER_TOKEN` | `****` | Short-lived; don't show even briefly |
| `REMOVE_TOKEN` | `****` | Short-lived; don't show even briefly |

Rules:
- In **plan mode previews** and **What we'll do** tables: use the variable name (`$SNOWFLAKE_ACCOUNT`) or `<placeholder>`, never the resolved value.
- In **What we did** summaries: confirm the secret was set (e.g. "✓ SNOWFLAKE_ACCOUNT secret set") — never print the value.
- When capturing output that may contain a token (e.g. `gh api .../registration-token`), assign to a shell variable immediately and do not print it in conversation.

## Resume Detection

Run this **before** the Prerequisites Check on every invocation.

```bash
# 1. Check for manifest inside an existing cloned repo
MANIFEST_IN_REPO=$(find . -maxdepth 2 -name "manifest.toml" -path "*/.coco-agent/*" 2>/dev/null | head -1)
# 2. Check for draft manifest written after inputs but before clone
MANIFEST_DRAFT=$(find ".coco-agent" -name "manifest.toml" -maxdepth 2 2>/dev/null | head -1)
```

If either is found:
```bash
python3 - <<'EOF'
import tomllib, datetime
from pathlib import Path

manifest_path = "$MANIFEST_IN_REPO" or "$MANIFEST_DRAFT"
m = tomllib.load(open(manifest_path, 'rb'))

print(f"\n{'='*55}")
print(f"  Manifest found: {manifest_path}")
print(f"  Project : {m['project']['repo_url'] or m['project']['repo_name']}")
print(f"  Prefix  : {m['project']['prefix']}")
print(f"  Platform: {m['project']['platform']}")
print(f"\n  Step progress:")
for k in sorted(m['steps']):
    s = m['steps'][k]
    age = ""
    if s['completed_at']:
        secs = (datetime.datetime.now(datetime.timezone.utc) -
                datetime.datetime.fromisoformat(s['completed_at'])).total_seconds()
        age = f"  ({secs/60:.0f}m ago)"
    icon = {"COMPLETE":"✓","IN_PROGRESS":"→","PENDING":"○","SKIPPED":"–"}.get(s['status'],"?")
    print(f"    {icon}  {k}: {s['label']} [{s['status']}]{age}")
print(f"{'='*55}\n")
EOF
```

If manifest found: load all values (`PREFIX`, `REPO_NAME`, `REPO_PATH`, `REPO_VISIBILITY`, `SKILL_MODE`, `RUNNER_PID`) — **skip re-asking any question whose value is already in the manifest**. Route to first step where `status != "COMPLETE"`. An `IN_PROGRESS` step means it crashed mid-execution — re-run from the start of that step.

If no manifest found: proceed normally to Prerequisites Check and input collection.

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

Read `skills/scaffold/references/run-mode.md` and follow Steps A–D before
collecting any other inputs:
- Step A sets `$SKILL_MODE`
- Step B generates the petname for the repo name `defaultValue`
- Step C detects Snowflake username → `$PREFIX`
- Step D detects or asks for `$SNOWFLAKE_ACCOUNT`

Also read `skills/scaffold/references/output-format.md` (formatting rules).

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

3. Use the petname from Step B of `run-mode.md` as the `defaultValue`.
   Track the generated name as `GENERATED_PETNAME` for conflict detection.

---

## Write Draft Manifest

Immediately after all inputs are collected — **before** calling `enter_plan_mode` for Create Project — write the draft manifest so the session is recoverable even if the user stops before the repo is created.

```bash
ISO_NOW=$(python3 -c "import datetime; print(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")
mkdir -p ".coco-agent/$REPO_NAME"
chmod 700 ".coco-agent/$REPO_NAME"
```

Write `.coco-agent/$REPO_NAME/manifest.toml` (substitute all `$VARIABLES` with collected values):

```toml
schema_version = "1"

[config]
stale_threshold_s        = 3600
runner_stale_threshold_s = 300

[template]
name       = "github-coco-agent"
repo_url   = "https://github.com/Snowflake-Labs/github-coco-agent"
ref        = "main"
cloned_at  = ""

[project]
platform   = "github"
prefix     = "$PREFIX"
repo_path  = ""
repo_name  = "$REPO_NAME"
repo_url   = ""
visibility = "$REPO_VISIBILITY"
run_mode   = "$SKILL_MODE"
created_at = "$ISO_NOW"

[snowflake]
user      = ""
role      = ""
warehouse = ""

[runner]
installed  = false
pid        = 0
runner_id  = ""

[steps.step_1]
label        = "Create Project"
status       = "PENDING"
started_at   = ""
completed_at = ""

[steps.step_2]
label        = "Hold Before Go-Live"
status       = "PENDING"
started_at   = ""
completed_at = ""

[steps.step_3]
label        = "Connect Snowflake"
status       = "PENDING"
started_at   = ""
completed_at = ""

[steps.step_4]
label        = "Configure"
status       = "PENDING"
started_at   = ""
completed_at = ""

[steps.step_5]
label        = "Watch the Loop"
status       = "PENDING"
started_at   = ""
completed_at = ""
```

```bash
chmod 600 ".coco-agent/$REPO_NAME/manifest.toml"
```

> Resume rule: on any future session, if `.coco-agent/$REPO_NAME/manifest.toml` or
> `$REPO_NAME/.coco-agent/manifest.toml` is found, read all values from it and skip
> re-asking inputs. Route to the first step whose status is not `"COMPLETE"`.

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

Also run to show the template structure:
```bash
gh repo view https://github.com/Snowflake-Labs/github-coco-agent
```
Display the description and file tree so the user can review before confirming.

Call `exit_plan_mode`. Then execute directly:

Mark step started — update `.coco-agent/$REPO_NAME/manifest.toml`:
```bash
python3 -c "
import re, datetime
from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('.coco-agent/$REPO_NAME/manifest.toml')
t = p.read_text()
t = re.sub(r'(\[steps\.step_1\][^\[]*?)status\s*=\s*\"PENDING\"', r'\1status       = \"IN_PROGRESS\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_1\][^\[]*?)started_at\s*=\s*\"\"', rf'\1started_at   = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
"
```

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

Move draft manifest into the cloned repo and fill repo identity:
```bash
REPO_URL=$(gh repo view "$REPO_PATH" --json url -q .url)
mkdir -p "$REPO_NAME/.coco-agent"
chmod 700 "$REPO_NAME/.coco-agent"
mv ".coco-agent/$REPO_NAME/manifest.toml" "$REPO_NAME/.coco-agent/manifest.toml"
rmdir ".coco-agent/$REPO_NAME" 2>/dev/null; rmdir ".coco-agent" 2>/dev/null || true
chmod 600 "$REPO_NAME/.coco-agent/manifest.toml"
python3 -c "
import re, datetime
from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml')
t = p.read_text()
t = t.replace('repo_path  = \"\"', 'repo_path  = \"$REPO_PATH\"')
t = t.replace('repo_url   = \"\"', 'repo_url   = \"$REPO_URL\"', 1)
t = t.replace('cloned_at  = \"\"', f'cloned_at  = \"{now}\"')
t = re.sub(r'(\[steps\.step_1\][^\[]*?)status\s*=\s*\"IN_PROGRESS\"', r'\1status       = \"COMPLETE\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_1\][^\[]*?)completed_at\s*=\s*\"\"', rf'\1completed_at = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
print('✓ Manifest written to $REPO_NAME/.coco-agent/manifest.toml')
"
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

---

## Hold Before Go-Live

**Gate check (staleness-aware):**
```bash
# Check manifest first — skip API call if step_1 completed within stale_threshold_s
python3 -c "
import tomllib, datetime
from pathlib import Path
p = Path('$REPO_NAME/.coco-agent/manifest.toml')
if p.exists():
    m = tomllib.load(p.open('rb'))
    s = m['steps']['step_1']
    if s['status'] == 'COMPLETE' and s['completed_at']:
        age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(s['completed_at'])).total_seconds()
        if age < m['config']['stale_threshold_s']:
            print(f'Using manifest cache ({age:.0f}s old) — repo verified'); exit(0)
print('RECHECK')
" || { gh api "repos/$REPO_PATH" --jq .name 2>&1 && ls "$REPO_NAME" 2>&1; }
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

Call `exit_plan_mode`. Then execute directly:

Mark step started:
```bash
python3 -c "
import re, datetime; from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml'); t = p.read_text()
t = re.sub(r'(\[steps\.step_2\][^\[]*?)status\s*=\s*\"PENDING\"', r'\1status       = \"IN_PROGRESS\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_2\][^\[]*?)started_at\s*=\s*\"\"', rf'\1started_at   = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
"
```

```bash
gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```
Expected: `false`. If `true`, Actions were re-enabled somehow — re-disable:
```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<'EOF'
{"enabled": false}
EOF
```

Mark step complete:
```bash
python3 -c "
import re, datetime; from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml'); t = p.read_text()
t = re.sub(r'(\[steps\.step_2\][^\[]*?)status\s*=\s*\"IN_PROGRESS\"', r'\1status       = \"COMPLETE\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_2\][^\[]*?)completed_at\s*=\s*\"\"', rf'\1completed_at = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
"

### What we did
- Confirmed GitHub Actions are disabled on `$REPO_PATH`
- No workflows will fire until Watch the Loop re-enables them

---

## Connect Snowflake

**Gate check (staleness-aware):**
```bash
python3 -c "
import tomllib, datetime; from pathlib import Path
p = Path('$REPO_NAME/.coco-agent/manifest.toml')
if p.exists():
    m = tomllib.load(p.open('rb')); s = m['steps']['step_2']
    if s['status'] == 'COMPLETE' and s['completed_at']:
        age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(s['completed_at'])).total_seconds()
        if age < m['config']['stale_threshold_s']:
            print(f'Using manifest cache ({age:.0f}s old) — Actions-disabled verified'); exit(0)
print('RECHECK')
" || gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
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
| Auth | `TYPE = SERVICE`, `WORKLOAD_IDENTITY = (TYPE = OIDC ISSUER = https://token.actions.githubusercontent.com)` |
| Subject | `repo:$REPO_PATH:ref:refs/heads/main` |

Also read and display `$REPO_NAME/snowflake/setup.sql` with variables substituted
so the user can review the exact SQL before confirming.

Call `exit_plan_mode`. Then execute directly:

Mark step started:
```bash
python3 -c "
import re, datetime; from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml'); t = p.read_text()
t = re.sub(r'(\[steps\.step_3\][^\[]*?)status\s*=\s*\"PENDING\"', r'\1status       = \"IN_PROGRESS\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_3\][^\[]*?)started_at\s*=\s*\"\"', rf'\1started_at   = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
"
```

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

Mark step complete + fill Snowflake section:
```bash
python3 -c "
import re, datetime; from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml'); t = p.read_text()
t = t.replace('user      = \"\"', 'user      = \"${PREFIX}_GITHUB_COCO_AGENT_USER\"')
t = t.replace('role      = \"\"', 'role      = \"${PREFIX}_GITHUB_COCO_AGENT_ROLE\"')
t = t.replace('warehouse = \"\"', 'warehouse = \"${PREFIX}_GITHUB_COCO_AGENT_WH\"')
t = re.sub(r'(\[steps\.step_3\][^\[]*?)status\s*=\s*\"IN_PROGRESS\"', r'\1status       = \"COMPLETE\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_3\][^\[]*?)completed_at\s*=\s*\"\"', rf'\1completed_at = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
print('✓ Snowflake section updated in manifest')
"
```

### What we did
- Role, warehouse, and `SERVICE` user with `WORKLOAD_IDENTITY` OIDC config created and verified
- Subject claim bound to `repo:$REPO_PATH:ref:refs/heads/main`

---

## Configure

**Gate check (staleness-aware):**
```bash
python3 -c "
import tomllib, datetime; from pathlib import Path
p = Path('$REPO_NAME/.coco-agent/manifest.toml')
if p.exists():
    m = tomllib.load(p.open('rb')); s = m['steps']['step_3']
    if s['status'] == 'COMPLETE' and s['completed_at']:
        age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(s['completed_at'])).total_seconds()
        if age < m['config']['stale_threshold_s']:
            print(f'Using manifest cache ({age:.0f}s old) — Snowflake user verified'); exit(0)
print('RECHECK')
" || snow sql -q "DESC USER ${PREFIX}_GITHUB_COCO_AGENT_USER" --format json 2>&1
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

Call `exit_plan_mode`. Then execute directly:

Mark step started:
```bash
python3 -c "
import re, datetime; from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml'); t = p.read_text()
t = re.sub(r'(\[steps\.step_4\][^\[]*?)status\s*=\s*\"PENDING\"', r'\1status       = \"IN_PROGRESS\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_4\][^\[]*?)started_at\s*=\s*\"\"', rf'\1started_at   = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
"
```

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

Call `exit_plan_mode`. Then execute directly:

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

Start the runner in the background (safe across chat steps — won't be killed when you move to the next step):
```bash
nohup "$REPO_NAME/.github/runner/run.sh" \
  > "$REPO_NAME/.github/runner/runner.log" 2>&1 &
RUNNER_PID=$!
echo $RUNNER_PID > "$REPO_NAME/.github/runner/runner.pid"
sleep 3
grep -q "Listening for Jobs" "$REPO_NAME/.github/runner/runner.log" \
  && echo "✓ Runner is listening (PID $RUNNER_PID)" \
  || echo "Still starting — check: tail -f $REPO_NAME/.github/runner/runner.log"
```

Persist PID and mark configure complete in manifest:
```bash
python3 -c "
import re, datetime; from pathlib import Path
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p = Path('$REPO_NAME/.coco-agent/manifest.toml'); t = p.read_text()
t = t.replace('installed  = false', 'installed  = true')
t = re.sub(r'pid\s*=\s*0', f'pid        = $RUNNER_PID', t)
t = re.sub(r'(\[steps\.step_4\][^\[]*?)status\s*=\s*\"IN_PROGRESS\"', r'\1status       = \"COMPLETE\"', t, flags=re.DOTALL)
t = re.sub(r'(\[steps\.step_4\][^\[]*?)completed_at\s*=\s*\"\"', rf'\1completed_at = \"{now}\"', t, flags=re.DOTALL)
p.write_text(t)
print(f'✓ Runner PID $RUNNER_PID persisted in manifest')
"
```

> `runner.pid` and `runner.log` are inside `.github/runner/` which is gitignored.
> To stop later: `kill $(cat $REPO_NAME/.github/runner/runner.pid)`

Then ask:
```
ask_user_question:
  header: "Start runner"
  question: "Runner started in background. Confirmed listening?"
  options:
    - label: "Yes, runner is listening — continue"
    - label: "Not yet — show runner log"
    - label: "Stop here"
```

If "Not yet — show runner log":
```bash
tail -20 "$REPO_NAME/.github/runner/runner.log"
```
Re-ask until confirmed.

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
- Runner PID persisted in `.coco-agent/manifest.toml`

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

**Enable Actions first** (must happen before the runner can pick up jobs):
```bash
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT \
  --input - <<'EOF'
{"enabled": true}
EOF
```

**Gate check (staleness-aware, if local runner was set up):**
```bash
python3 -c "
import tomllib, datetime; from pathlib import Path
p = Path('$REPO_NAME/.coco-agent/manifest.toml')
if p.exists():
    m = tomllib.load(p.open('rb'))
    if m['runner']['pid'] > 0:
        s = m['steps']['step_4']
        if s['status'] == 'COMPLETE' and s['completed_at']:
            age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(s['completed_at'])).total_seconds()
            if age < m['config']['runner_stale_threshold_s']:
                print(f'Using manifest cache ({age:.0f}s old) — runner verified'); exit(0)
print('RECHECK')
" || gh api "repos/$REPO_PATH/actions/runners" --jq '.runners | length'
```
If 0:
> ⚠️ **Gate check failed:** No runner is online.
> Check: `tail -f $REPO_NAME/.github/runner/runner.log`
> Restart: `nohup $REPO_NAME/.github/runner/run.sh > $REPO_NAME/.github/runner/runner.log 2>&1 & echo $! > $REPO_NAME/.github/runner/runner.pid`

---

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> The smoke-test app contains 3 intentional security and correctness issues.
> Running it proves the loop end-to-end: scan finds issues, fix agents patch
> them, PRs are opened automatically. No production code is touched.

**What we'll do**
```
Step 1: write smoke-test app (3 files) to $REPO_NAME/demo/
Step 2: commit + push  →  scan workflow triggers on the runner
Step 3: show Actions URL
Step 4: revert when done  (git revert HEAD --no-edit && git push)
```

Call `exit_plan_mode`. Then execute directly:

**Step 1 — Copy templates:**
Read `skills/scaffold/references/smoke-test.md` and write the files from
`skills/scaffold/templates/smoke-test/` to `$REPO_NAME/demo/`.

**Step 2 — Commit and push:**
```bash
cd "$REPO_NAME"
git add demo/
git commit -m "test(smoke): add intentional-issue app for CI/CD loop validation"
git push
```

**Step 3 — Show Actions URL:**
```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
```

**Step 4 — Revert when done** (run after the loop has validated):
```bash
cd "$REPO_NAME"
git revert HEAD --no-edit && git push
```

### What we did
- Actions enabled on `$REPO_PATH`
- Smoke-test app pushed to `demo/` — scan workflow triggered on the runner
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
      description: "Drop Snowflake resources, delete GitHub repo, and remove local clone"
    - label: "Drop Snowflake only"
      description: "Keep repo and local clone; drop Snowflake objects and deregister runner"
    - label: "Keep everything"
```

If "Keep everything" → stop.

**Pre-flight: read manifest (or ask if missing)**
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
if [ -f "$MANIFEST" ]; then
  PREFIX=$(python3 -c "import tomllib; m=tomllib.load(open('$MANIFEST','rb')); print(m['project']['prefix'])")
  REPO_PATH=$(python3 -c "import tomllib; m=tomllib.load(open('$MANIFEST','rb')); print(m['project']['repo_path'])")
  REPO_URL=$(python3 -c "import tomllib; m=tomllib.load(open('$MANIFEST','rb')); print(m['project']['repo_url'])")
  RUNNER_PID=$(python3 -c "import tomllib; m=tomllib.load(open('$MANIFEST','rb')); print(m['runner']['pid'])")
  RUNNER_INSTALLED=$(python3 -c "import tomllib; m=tomllib.load(open('$MANIFEST','rb')); print(m['runner']['installed'])")
  echo "✓ Manifest loaded: PREFIX=$PREFIX REPO_PATH=$REPO_PATH RUNNER_PID=$RUNNER_PID"
else
  echo "No manifest found — enter values manually"
  # ask_user_question for PREFIX and REPO_PATH
fi
```

⚠️ MANDATORY: call `enter_plan_mode` now. Then present:

**Why this matters** (Guided mode only):
> Resources left running after a demo cost credits. Teardown runs in dependency
> order: disable CI first so no new jobs fire, then stop and deregister the runner,
> then drop Snowflake objects, then delete the remote repo, then remove the local clone.
> Skipping any step leaves orphaned objects.

**What we'll drop**
```
[if "tear down everything"]
  1. Disable Actions            (no new workflow runs during teardown)
  2. Kill runner process        (PID: $RUNNER_PID — if runner installed)
  3. Deregister runner          (from GitHub API — if runner installed)
  4. Drop Snowflake:
       DROP USER      IF EXISTS ${PREFIX}_GITHUB_COCO_AGENT_USER;
       DROP WAREHOUSE IF EXISTS ${PREFIX}_GITHUB_COCO_AGENT_WH;
       DROP ROLE      IF EXISTS ${PREFIX}_GITHUB_COCO_AGENT_ROLE;
  5. Delete remote:  $REPO_URL
  6. Delete local:   ./$REPO_NAME/  (manifest included)

[if "Drop Snowflake only"]
  1. Kill runner process        (PID: $RUNNER_PID — if runner installed)
  2. Deregister runner + restore ubuntu-latest workflows + push
  3. Disable Actions            (no live runner to serve jobs)
  4. Drop Snowflake (same 3 objects)
  5. Remove .coco-agent/        (manifest deleted — repo kept)
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

**Execute — "tear down everything":**
```bash
# 1. Disable Actions
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT --input - <<<'{"enabled": false}'

# 2. Kill runner process
if [ "${RUNNER_PID:-0}" -gt 0 ]; then
  kill "$RUNNER_PID" 2>/dev/null || true; sleep 2
fi

# 3. Deregister runner (no workflow patch — repo being deleted)
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
fi

# 4. Drop Snowflake resources
snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"

# 5. Delete remote repo
gh repo delete "$REPO_PATH" --yes

# 6. Delete local clone (manifest inside — gone with it)
rm -rf "$REPO_NAME"
# Also clean up CWD draft manifest if it exists
rm -rf ".coco-agent/$REPO_NAME" 2>/dev/null; rmdir ".coco-agent" 2>/dev/null || true
echo "✓ $REPO_NAME removed — environment is clean"
```

**Execute — "Drop Snowflake only":**
```bash
# 1. Kill runner process
if [ "${RUNNER_PID:-0}" -gt 0 ]; then
  kill "$RUNNER_PID" 2>/dev/null || true; sleep 2
fi

# 2. Deregister runner + restore workflows + push
if [ -f "$REPO_NAME/.github/runner/config.sh" ]; then
  REMOVE_TOKEN=$(gh api "repos/$REPO_PATH/actions/runners/remove-token" -X POST -q .token)
  "$REPO_NAME/.github/runner/config.sh" remove --token "$REMOVE_TOKEN"
  sed -i '' 's/runs-on: \[self-hosted, local\]/runs-on: ubuntu-latest/g' \
    "$REPO_NAME/.github/workflows/cortex-scan.yml" \
    "$REPO_NAME/.github/workflows/cortex-fix.yml"
  git -C "$REPO_NAME" add .github/workflows/
  git -C "$REPO_NAME" commit -m "ci(workflows): restore ubuntu-latest runner [skip ci]"
  git -C "$REPO_NAME" push
fi

# 3. Disable Actions
gh api "repos/$REPO_PATH/actions/permissions" \
  -X PUT --input - <<<'{"enabled": false}'

# 4. Drop Snowflake resources
snow sql -f "$REPO_NAME/snowflake/teardown.sql" -D "PREFIX=$PREFIX"

# 5. Remove manifest (marks setup as torn down — repo kept)
rm -rf "$REPO_NAME/.coco-agent/"
echo "✓ Snowflake resources dropped. Repo kept at $REPO_URL"
```

### What we did
- CI disabled (Actions blocked)
- Runner stopped and deregistered (if installed)
- Snowflake objects dropped: `${PREFIX}_GITHUB_COCO_AGENT_USER / _WH / _ROLE`
- [tear down everything] Repo deleted and local clone removed
- [Drop Snowflake only] Manifest removed — re-run scaffold to set up again

> ✓ **Done:** Environment is clean.
