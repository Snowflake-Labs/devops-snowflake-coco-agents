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

## Step Order

⚠️ MANDATORY: Execute steps 1–6 in order. Never skip or reorder.
Each step builds on the previous — jumping ahead leaves the repo in a broken state.

## Forbidden Actions

⚠️ FORBIDDEN:
- Do not modify the template repo (`https://github.com/Snowflake-Labs/github-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set GitHub secrets other than the four listed in Configure.
- Do not enable Actions before Configure is complete.
- **NEVER auto-merge PRs** — always require human review before merging fix PRs.

## Sensitive Values

⚠️ NEVER echo real values — use variable names or placeholders:

| Variable | Mask as |
|----------|---------|
| `SNOWFLAKE_ACCOUNT` | `<account>` |
| `RUNNER_TOKEN` | `****` |
| `REMOVE_TOKEN` | `****` |

In plan mode previews, use `$VARIABLE` not the resolved value. In "What we did" summaries confirm set without showing the value.

See `skills/scaffold/references/token-scopes.md` for required token scopes.

## Resume Detection

First action on every invocation — before Prerequisites. Read `skills/scaffold/references/manifest.md` for SKILL_DIR resolution.

```bash
# Resolve SKILL_DIR (works for any install path — see references/manifest.md)
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
REPO_NAME=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_name 2>/dev/null)
REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path 2>/dev/null)
SKILL_MODE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.run_mode 2>/dev/null)
```

Skip re-asking any question already in the manifest. Route to first step where `status != "COMPLETE"`. `IN_PROGRESS` = crashed mid-execution — re-run from start of that step.

If `$MANIFEST` is empty — check for orphaned resources before starting fresh:
```bash
ORPHANED=$(snow sql -q "SHOW USERS LIKE '%_GH_%_COCO_AGENT_USER'" --format json 2>/dev/null | python3 -c "import sys,json; r=json.load(sys.stdin); print(len(r))" 2>/dev/null || echo 0)
```
If `$ORPHANED` > 0:
> ⚠️ **No manifest found but existing CoCo Snowflake resources were detected.**
> Starting fresh may leave orphaned objects. Options:
> - Run Step 6 (Clean Up) first to drop them, then re-scaffold
> - Continue anyway (orphaned objects remain until manually cleaned up)

## Prerequisites Check

Run before collecting inputs. If either fails, stop and help before proceeding.

**Check 1 — gh CLI:**
```bash
gh auth status 2>&1
```
If not authenticated, ask:
```
ask_user_question:
  header: "gh CLI required"
  question: "gh is not authenticated. Install gh (https://cli.github.com) and run 'gh auth login', then come back."
  options:
    - label: "Done, I've authenticated"
    - label: "Abort"
```

**Multi-account:** parse `gh auth status` for lines matching `"Logged in to github.com account <name>"`. If multiple accounts, ask which to use:
```
ask_user_question:
  header: "GitHub account"
  question: "Multiple GitHub accounts found. Which one should be used?"
  defaultAnswer: "<active account>"
  options: [one per detected account]
```
If switching: `gh auth switch --user <chosen>` → confirm: `gh api user --jq .login`

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
      description: "Steps 1-3 + secrets → re-enable CI → done in ~10 min. Works for new repos and existing ones."
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
     question: "Create a new GitHub repo from template, or add CoCo to an existing repo?"
     options:
       - label: "New repo (from template)"
       - label: "Add to existing repo"
   ```
   If "Add to existing repo": set `IMPORT_MODE = true`. Skip stopping points 1–2. Ask:
   ```
   ask_user_question:
     header: "Existing repo"
     question: "Which repo should CoCo be added to?"
     type: text
     defaultValue: "<login>/my-repo"
   ```
   Verify: `gh api "repos/$REPO_PATH" --jq '{name,visibility}'` — must succeed.
   Set `REPO_NAME="${REPO_PATH##*/}"`. Skip draft manifest and go directly to step-1 import path.

1. **Target repo** — detect login: `gh api user --jq .login`. Use petname as `defaultValue`.
   ```
   ask_user_question:
     header: "New repo"
     question: "Confirm the repo name, or type a new one:"
     type: text
     defaultValue: "<login>/<petname>"
   ```
   Track: `USING_GENERATED = true` if unchanged, `false` if edited.

2. **Visibility** — detect org: `gh api "orgs/${REPO_PATH%%/*}" 2>/dev/null`
   - Personal: Private / Public (default: Private)
   - Org: Private / Internal / Public (default: Private)
   Store as `$REPO_VISIBILITY`. Flag: Private→`--private`, Internal→`--internal`, Public→`--public`.

## Write Draft Manifest

Immediately after all inputs collected — before Step 1 plan mode.
See `skills/scaffold/references/manifest.md` for SKILL_DIR resolution.

```bash
python3 "$MANIFEST_OPS" init \
  --draft-path ".coco-agent/$REPO_NAME" \
  --prefix     "$PREFIX" \
  --repo-name  "$REPO_NAME" \
  --visibility "$REPO_VISIBILITY" \
  --run-mode   "$SKILL_MODE" \
  --platform   "github" \
  --template-name "github-coco-agent"
```

## Steps

Execute each step by loading the corresponding file. Steps must be executed in order.

| Step | File | Mode |
|------|------|------|
| 1. Create Project | `skills/scaffold/github/steps/step-1-create-project.md` | both |
| 2. Hold Before Go-Live | `skills/scaffold/github/steps/step-2-hold-before-golive.md` | both |
| 3. Connect Snowflake | `skills/scaffold/github/steps/step-3-connect-snowflake.md` | both |
| 4. Configure | `skills/scaffold/github/steps/step-4-configure.md` | both (routes by SETUP_MODE) |
| 5. Watch the Loop | `skills/scaffold/github/steps/step-5-watch-loop.md` | full only |
| 6. Clean Up | `skills/scaffold/github/steps/step-6-clean-up.md` | on demand |

Load each step file and execute it fully before proceeding to the next.
