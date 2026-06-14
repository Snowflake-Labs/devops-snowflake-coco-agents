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
- Do not modify the template project (`https://gitlab.com/kameshsampath/gitlab-coco-agent`) itself.
- Do not create Snowflake objects beyond what `snowflake/setup.sql` provisions.
- Do not set CI/CD variables other than the four listed in Configure.
- Do not enable pipelines before Configure is complete.
- **NEVER modify the local runner's environment** — no `uv tool uninstall`, no `pip uninstall`, no `brew uninstall`, no overwriting `~/.snowflake/connections.toml`. Local runners use what is already installed. The three-branch `*write_connection` anchor enforces this: if neither `$SNOWFLAKE_TOKEN` nor `$SNOWFLAKE_PAT` is set, the existing connections.toml is used untouched.

## Sensitive Values

⚠️ NEVER echo real values — use variable names or placeholders:

| Variable | Mask as |
|----------|---------|
| `SNOWFLAKE_ACCOUNT` | `<account>` |
| `GITLAB_TOKEN_coco` | `****` |
| `RUNNER_TOKEN` | `****` |
| `REMOVE_TOKEN` | `****` |

`GITLAB_TOKEN_coco` is write-only after capture — never display after collection.

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

## Prerequisites Check

Run before collecting inputs.

**Check 1 — glab CLI:**
```bash
glab auth status 2>&1
```
If not authenticated, ask user to run `glab auth login` and retry.

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

1. **Target project** — detect username: `glab api user --field username`. Use petname as `defaultValue`.
   ```
   ask_user_question:
     header: "New project"
     question: "Full path for the new project? (generated suggestion — edit freely)"
     type: text
     defaultValue: "<username>/<petname>"
   ```
   Track: `USING_GENERATED = true` if unchanged, `false` if edited.

2. **Visibility** — always pass the flag explicitly (glab defaults to `--internal`):
   Private / Internal / Public (default: Private)
   Store as `$PROJECT_VISIBILITY`. Flag: Private→`--private`, Internal→`--internal`, Public→`--public`.

3. **GitLab bot token** — detection chain (run in order, stop at first match):

   ```bash
   GITLAB_TOKEN_coco=""

   # Level 1: env var already exported
   [ -n "${GITLAB_TOKEN:-}" ] && GITLAB_TOKEN_coco="$GITLAB_TOKEN" && echo "✓ Found GITLAB_TOKEN in env"

   # Level 2: .envrc (active or commented)
   if [ -z "$GITLAB_TOKEN_coco" ] && grep -q "GITLAB_TOKEN" .envrc 2>/dev/null; then
     _VAL=$(grep "GITLAB_TOKEN" .envrc | grep -v "^#" | head -1 | cut -d= -f2- | tr -d ' "')
     [ -n "$_VAL" ] && GITLAB_TOKEN_coco="$_VAL" && echo "✓ Found GITLAB_TOKEN in .envrc"
   fi

   # Level 3: macOS Keychain (where glab auth login stores the token)
   if [ -z "$GITLAB_TOKEN_coco" ]; then
     _VAL=$(security find-generic-password -s "glab:https://gitlab.com" -w 2>/dev/null || true)
     [ -n "$_VAL" ] && GITLAB_TOKEN_coco="$_VAL" && echo "✓ Found token in Keychain (glab)"
   fi
   ```

   If `GITLAB_TOKEN_coco` still empty — ask:
   ```
   ask_user_question:
     header: "GitLab token"
     question: "No GITLAB_TOKEN found. How would you like to provide one?"
     options:
       - label: "Open GitLab to create a new token"
         description: "Opens token creation page with name and scopes pre-filled"
       - label: "I already have a token"
   ```
   If "Open GitLab": open `https://gitlab.com/-/user_settings/personal_access_tokens?name=coco-bot&scopes=api,write_repository`

   Once token is available — ask type (affects scope instructions only):
   ```
   ask_user_question:
     header: "Token type"
     question: "Classic PAT or fine-grained token?"
     options:
       - label: "Classic PAT (api + write_repository scopes)"
       - label: "Fine-grained token (Repository R/W, Issues R/W, MR R/W, CI/CD R/W)"
   ```

   **Store securely (no echo):**
   ```bash
   cortex secret store gitlab-token-coco --prompt
   ```
   From this point: all bash calls that need the token use `secret_env: {"GITLAB_TOKEN": "gitlab-token-coco"}`.
   `glab` reads `GITLAB_TOKEN` from env automatically — no `--header` or `--token` flag needed.

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

| Step | File |
|------|------|
| 1. Create Project | `skills/scaffold/gitlab/steps/step-1-create-project.md` |
| 2. Hold Before Go-Live | `skills/scaffold/gitlab/steps/step-2-hold-before-golive.md` |
| 3. Connect Snowflake | `skills/scaffold/gitlab/steps/step-3-connect-snowflake.md` |
| 4. Configure | `skills/scaffold/gitlab/steps/step-4-configure.md` |
| 5. Watch the Loop | `skills/scaffold/gitlab/steps/step-5-watch-loop.md` |
| 6. Clean Up | `skills/scaffold/gitlab/steps/step-6-clean-up.md` |

Load each step file and execute it fully before proceeding to the next.
