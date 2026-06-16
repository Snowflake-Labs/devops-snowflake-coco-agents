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
IS the single execute gate. After `exit_plan_mode`, execute directly.

## Step Order

⚠️ MANDATORY: Execute steps 1–6 in order. Never skip or reorder.
Each step builds on the previous — jumping ahead leaves the project in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template project (`https://gitlab.com/snowflake-dev/gitlab-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set CI/CD variables other than the four listed in Configure.
- Do not enable pipelines before Configure is complete.
- **NEVER auto-merge MRs** — always require human review before merging fix MRs.

## Sensitive Values

⚠️ NEVER echo real values — use variable names or placeholders:

| Variable | Mask as |
|----------|---------|
| `SNOWFLAKE_ACCOUNT` | `<account>` |
| `GITLAB_TOKEN_COCO` | `****` |
| `RUNNER_TOKEN` | `****` |
| `REMOVE_TOKEN` | `****` |

`GITLAB_TOKEN_COCO` is write-only after capture — never display after collection.
See `skills/scaffold/references/token-scopes.md` for required PAT scopes.

## Resume Detection

First action on every invocation — before Prerequisites. Read `skills/scaffold/references/manifest.md` for SKILL_DIR resolution.

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"

MANIFEST_IN_REPO=$(find . -maxdepth 2 -name "manifest.toml" -path "*/.coco-agent/*" 2>/dev/null | head -1)
MANIFEST_DRAFT=$(find ".coco-agent" -name "manifest.toml" -maxdepth 2 2>/dev/null | head -1)
MANIFEST="${MANIFEST_IN_REPO:-$MANIFEST_DRAFT}"
```

If `$MANIFEST` is non-empty:
```bash
python3 "$MANIFEST_OPS" summary --manifest "$MANIFEST"
PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix 2>/dev/null)
PROJECT_NAME=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_name 2>/dev/null)
PROJECT_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path 2>/dev/null)
SKILL_MODE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.run_mode 2>/dev/null)
```

Skip re-asking any question already in the manifest. Route to first step where `status != "COMPLETE"`. `IN_PROGRESS` = crashed — re-run from start of that step.

If `$MANIFEST` is empty — check for orphaned resources before starting fresh:
```bash
ORPHANED=$(snow sql -q "SHOW USERS LIKE '%_GL_%_COCO_AGENT_USER'" --format json 2>/dev/null | python3 -c "import sys,json; r=json.load(sys.stdin); print(len(r))" 2>/dev/null || echo 0)
```
If `$ORPHANED` > 0:
> ⚠️ **No manifest found but existing CoCo Snowflake resources were detected.**
> Starting fresh may leave orphaned objects. Options:
> - Run Step 6 (Clean Up) first to drop them, then re-scaffold
> - Continue anyway (orphaned objects remain until manually cleaned up)

## Prerequisites Check

Run before collecting inputs.

**Check 1 — glab auth (mandatory hard gate):**
```bash
glab auth status 2>&1
```
If output does NOT contain `"Logged in to gitlab.com"`:
> ⚠️ **STOP:** Not authenticated to GitLab.
> Run `glab auth login --hostname gitlab.com` then re-invoke this skill.

Do NOT continue until authenticated. All `glab api` commands in this skill
use the stored session automatically — no manual token passing needed.

**Multi-account:** parse `glab auth status` for `"Logged in to gitlab.com as <username>"`. Always confirm:
```
ask_user_question:
  header: "GitLab account"
  question: "Currently logged into GitLab as <username>. Use this account?"
  options:
    - label: "Yes, use <username>"
    - label: "Switch to a different account"
```
If switching: `glab auth logout --hostname gitlab.com && glab auth login --hostname gitlab.com`

**Check 2 — snow CLI:**
```bash
snow connection test
```
If fails, ask user to configure `~/.snowflake/connections.toml` and retry.

**Check 3 — git:**
```bash
git --version 2>&1
```
If missing, ask user to install git and retry.

**Check 4 — python3 (3.11+):**
```bash
python3 --version 2>&1
```
If missing or below 3.11, ask user to install Python 3.11+ and retry.

## Setup Mode

Ask once — before collecting project inputs:

```
ask_user_question:
  header: "Setup mode"
  question: "How would you like to set up CoCo?"
  options:
    - label: "Quick start — cloud runners"
      description: "Steps 1-3 + secrets → re-enable CI → done in ~10 min. Works for new projects and existing ones."
    - label: "Full setup — with smoke test"
      description: "All steps including an end-to-end validation run with a sample app."
```

Set `SETUP_MODE = "quick"` or `SETUP_MODE = "full"`.

## Run Mode, Project Name, and Output Format

Read `skills/scaffold/references/run-mode.md` (Steps A–D: sets `$SKILL_MODE`, `$PREFIX`, `$SNOWFLAKE_ACCOUNT`, petname).
Read `skills/scaffold/references/output-format.md` (formatting rules).

## Stopping Points

Collect all inputs before Create Project.

0. **Project type** — ask first:
   ```
   ask_user_question:
     header: "Project type"
     question: "Create a new GitLab project from template, or add CoCo to an existing one?"
     options:
       - label: "New project (from template)"
       - label: "Add to existing project"
   ```
   If "Add to existing project": set `IMPORT_MODE = true`. Skip stopping points 1–2. Ask:
   ```
   ask_user_question:
     header: "Existing project"
     question: "Which project should CoCo be added to? (namespace/project)"
     type: text
     defaultValue: "<username>/my-project"
   ```
   Verify: `glab api "projects/$ENCODED_PATH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['name'], d['visibility'])"` — must succeed.
   Set `PROJECT_NAME="${PROJECT_PATH##*/}"`. Skip draft manifest and go directly to step-1 import path.

1. **Target project** — detect username:
   ```bash
   GITLAB_USER=$(glab api user | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])")
   ```
   Use `$GITLAB_USER/<petname>` as `defaultValue`.
   ```
   ask_user_question:
     header: "New project"
     question: "Confirm the project path, or type a new one:"
     type: text
     defaultValue: "<username>/<petname>"
   ```
   Track: `USING_GENERATED = true` if unchanged, `false` if edited.

2. **Visibility** — always pass the flag explicitly (glab defaults to `--internal`):
   Private / Internal / Public (default: Private)
   Store as `$PROJECT_VISIBILITY`. Flag: Private→`--private`, Internal→`--internal`, Public→`--public`.

Derive: `GROUP="${PROJECT_PATH%/*}"`, `PROJECT_NAME="${PROJECT_PATH##*/}"`, `ENCODED_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PROJECT_PATH', safe=''))")`

## Write Draft Manifest

Immediately after all inputs collected — before Step 1 plan mode.
See `skills/scaffold/references/manifest.md` for SKILL_DIR resolution.

```bash
python3 "$MANIFEST_OPS" init \
  --draft-path ".coco-agent/$PROJECT_NAME" \
  --prefix     "$PREFIX" \
  --repo-name  "$PROJECT_NAME" \
  --visibility "$PROJECT_VISIBILITY" \
  --run-mode   "$SKILL_MODE" \
  --platform   "gitlab" \
  --template-name "gitlab-coco-agent"
```

## Steps

Execute each step by loading the corresponding file. Steps must be executed in order.

| Step | File | Mode |
|------|------|------|
| 1. Create Project | `skills/scaffold/gitlab/steps/step-1-create-project.md` | both |
| 2. Hold Before Go-Live | `skills/scaffold/gitlab/steps/step-2-hold-before-golive.md` | both |
| 3. Connect Snowflake | `skills/scaffold/gitlab/steps/step-3-connect-snowflake.md` | both |
| 4. Configure | `skills/scaffold/gitlab/steps/step-4-configure.md` | both (routes by SETUP_MODE) |
| 5. Watch the Loop | `skills/scaffold/gitlab/steps/step-5-watch-loop.md` | full only |
| 6. Clean Up | `skills/scaffold/gitlab/steps/step-6-clean-up.md` | on demand |

Load each step file and execute it fully before proceeding to the next.
