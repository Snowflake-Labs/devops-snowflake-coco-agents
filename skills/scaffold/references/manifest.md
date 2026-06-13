# Manifest Reference

Shared manifest operations for both the GitHub and GitLab scaffold skills.
Both skills use identical schema, SKILL_DIR resolution, and script invocations.

---

## SKILL_DIR Resolution

Run this once at the start of any step that calls `manifest_ops.py`.
Works regardless of how the plugin was installed (GitHub, local, fork).

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)

# Fallback: local dev checkout
if [ -z "$SKILL_DIR" ]; then
  SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
fi

MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
```

---

## Manifest Schema

File: `$REPO_NAME/.coco-agent/manifest.toml` (after clone)
Draft: `.coco-agent/$REPO_NAME/manifest.toml` (before clone)
Permissions: directory `700`, file `600` — set automatically by `manifest_ops.py`

```toml
# Machine-managed by Cortex Code. Do not hand-edit.
schema_version       = "1"

[config]
stale_threshold_s        = 3600   # gate check cache TTL (seconds)
runner_stale_threshold_s = 300    # runner status TTL (shorter — can go offline)

[template]
name       = "github-coco-agent"   # or "gitlab-coco-agent"
repo_url   = "https://github.com/Snowflake-Labs/github-coco-agent"
ref        = "main"
cloned_at  = ""                    # filled by: manifest_ops.py move

[project]
platform   = "github"              # or "gitlab"
prefix     = "ksampath"
repo_path  = ""                    # filled by: manifest_ops.py move
repo_name  = "ksampath-brave-lion"
repo_url   = ""                    # filled by: manifest_ops.py move
visibility = "private"
run_mode   = "guided"
created_at = "2026-06-13T10:00:00Z"

[snowflake]
# Derived from prefix — no sensitive values stored
user      = ""   # filled by: manifest_ops.py fill-snowflake
role      = ""
warehouse = ""

[runner]
installed  = false
pid        = 0    # filled by: manifest_ops.py fill-runner (at nohup launch)
runner_id  = ""   # GitLab: numeric ID for API delete; GitHub: empty

[steps.step_1]
label        = "Create Project"
status       = "PENDING"      # PENDING → IN_PROGRESS → COMPLETE | SKIPPED
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

---

## CLI Reference

All commands: `python3 "$MANIFEST_OPS" <command> [options]`

### init — write draft manifest after inputs collected

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

### move — after git clone, move draft into repo

```bash
REPO_URL=$(gh repo view "$REPO_PATH" --json url -q .url)
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$REPO_NAME" \
  --to   "$REPO_NAME/.coco-agent" \
  --repo-path "$REPO_PATH" \
  --repo-url  "$REPO_URL"
```

### step-start — mark a step IN_PROGRESS at execution start

```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_1
```

### step-complete — mark a step COMPLETE after gate check passes

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### fill-snowflake — fill [snowflake] after setup.sql runs

```bash
python3 "$MANIFEST_OPS" fill-snowflake \
  --manifest "$MANIFEST" \
  --prefix   "$PREFIX" \
  --platform "github"
# Writes: ${PREFIX}_GITHUB_COCO_AGENT_USER / _ROLE / _WH
```

### fill-runner — persist PID after nohup launch

```bash
nohup ".../run.sh" > runner.log 2>&1 &
RUNNER_PID=$!
echo $RUNNER_PID > runner.pid
python3 "$MANIFEST_OPS" fill-runner \
  --manifest   "$MANIFEST" \
  --pid        "$RUNNER_PID" \
  --runner-id  "$RUNNER_ID"   # GitLab only; omit or pass "" for GitHub
```

### read — read a single value (for teardown variable loading)

```bash
PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix)
REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
RUNNER_PID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.pid)
RUNNER_ID=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key runner.runner_id)
```

### summary — print step progress (resume detection)

```bash
python3 "$MANIFEST_OPS" summary --manifest "$MANIFEST"
```

Output:
```
========================================================
  Manifest : .coco-agent/manifest.toml
  Project  : https://github.com/org/repo-name
  Prefix   : ksampath
  Platform : github

  Step progress:
    ✓  step_1: Create Project [COMPLETE]  (5m ago)
    ✓  step_2: Hold Before Go-Live [COMPLETE]  (4m ago)
    →  step_3: Connect Snowflake [IN_PROGRESS]   ← crashed here
    ○  step_4: Configure [PENDING]
    ○  step_5: Watch the Loop [PENDING]
========================================================
```

### check-stale — gate check caching (exit 0 = cached, exit 1 = re-check)

```bash
# Use manifest cache if step N is COMPLETE and fresh; otherwise run API call
python3 "$MANIFEST_OPS" check-stale \
  --manifest "$MANIFEST" \
  --step     step_2 \
  || gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```

For the runner gate (shorter threshold):
```bash
python3 "$MANIFEST_OPS" check-stale \
  --manifest  "$MANIFEST" \
  --step      step_4 \
  --threshold 300 \
  || gh api "repos/$REPO_PATH/actions/runners" --jq '.runners | length'
```

---

## Resume Detection

Run at the top of every invocation (before Prerequisites Check):

```bash
MANIFEST_IN_REPO=$(find . -maxdepth 2 -name "manifest.toml" \
  -path "*/.coco-agent/*" 2>/dev/null | head -1)
MANIFEST_DRAFT=$(find ".coco-agent" -name "manifest.toml" \
  -maxdepth 2 2>/dev/null | head -1)

MANIFEST="${MANIFEST_IN_REPO:-$MANIFEST_DRAFT}"

if [ -n "$MANIFEST" ]; then
  python3 "$MANIFEST_OPS" summary --manifest "$MANIFEST"
  # Load stored values — skip re-asking these questions
  PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix 2>/dev/null)
  REPO_NAME=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_name 2>/dev/null)
  REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path 2>/dev/null)
  SKILL_MODE=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.run_mode 2>/dev/null)
fi
```

**Resume routing:**
- First step with `status = "IN_PROGRESS"` → crashed mid-execution, re-run from start of that step
- First step with `status = "PENDING"` after a run of `COMPLETE` → start here
- All `COMPLETE` → jump to Watch the Loop

---

## Step Boundary Pattern

Every step file uses this pattern:

```bash
# At step start (before any actions):
python3 "$MANIFEST_OPS" step-start   --manifest "$MANIFEST" --step step_N

# ... execute step actions ...

# After gate check passes (step is verified complete):
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_N
```

`IN_PROGRESS` + no `completed_at` = crash signal. `COMPLETE` + `completed_at` = gate check can be cached.
