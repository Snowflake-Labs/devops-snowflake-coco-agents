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

Step files reference this section instead of inlining the block. After resolving
SKILL_DIR, each step also sets the platform-specific manifest path:

- GitHub: `MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"`
- GitLab: `MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"`

---

## Connect Snowflake — OIDC Explanation

Shared "Why this matters" block for Step 3. The only difference between platforms
is the identity token source (runner identity vs CI job identity).

> WORKLOAD_IDENTITY replaces long-lived passwords with short-lived OIDC tokens.
> **{GitHub: the Actions runner / GitLab: the CI job}** proves its identity;
> Snowflake verifies the issuer and subject claim. No secret is ever stored.
>
> `SNOWFLAKE.CORTEX_USER` database role is also granted — unlocks Cortex AI
> endpoints. Without it, every `cortex exec` call returns 403 Forbidden.

---

## Manifest Schema

File: `$REPO_NAME/.coco-agent/manifest.toml` (after clone)
Draft: `.coco-agent/$REPO_NAME/manifest.toml` (before clone)
Permissions: directory `700`, file `600` — set automatically by `manifest_ops.py`

```toml
# Machine-managed by Cortex Code. Do not hand-edit.
schema_version       = "1"

[config]
stale_threshold_s = 3600   # gate check cache TTL (seconds)

[template]
name       = "github-coco-agent"   # or "gitlab-coco-agent"
repo_url   = "https://github.com/Snowflake-Labs/github-coco-agent"
ref        = "main"
cloned_at  = ""                    # filled by: manifest_ops.py move

[project]
platform   = "github"              # or "gitlab"
prefix     = "youruser"
repo_path  = ""                    # filled by: manifest_ops.py move
repo_name  = "youruser-brave-lion"
repo_url   = ""                    # filled by: manifest_ops.py move
visibility = "private"
run_mode   = "guided"
created_at = "2026-06-13T10:00:00Z"

[snowflake]
# Derived from prefix — no sensitive values stored
user      = ""   # filled by: manifest_ops.py fill-snowflake
role      = ""
warehouse = ""
oidc_subject = ""   # filled by: manifest_ops.py fill-oidc (subject confirmed in Step 2)

[steps.step_1]
label        = "Create Project"
status       = "PENDING"      # PENDING → IN_PROGRESS → COMPLETE | SKIPPED
started_at   = ""
completed_at = ""

[steps.step_2]
label        = "Connect Snowflake"
status       = "PENDING"
started_at   = ""
completed_at = ""

[steps.step_3]
label        = "Configure"
status       = "PENDING"
started_at   = ""
completed_at = ""

[steps.step_4]
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
# Writes: ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_USER / _ROLE / _WH
# Existing keys (e.g. oidc_subject) are preserved
```

### fill-oidc — record the OIDC subject the user confirmed

```bash
python3 "$MANIFEST_OPS" fill-oidc \
  --manifest "$MANIFEST" \
  --subject  "$OIDC_SUBJECT"
# Writes: snowflake.oidc_subject
```

### read — read a single value (for teardown variable loading)

```bash
PREFIX=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.prefix)
REPO_PATH=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" --key project.repo_path)
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
  Prefix   : youruser
  Platform : github

  Step progress:
    ✓  step_1: Create Project [COMPLETE]  (5m ago)
    →  step_2: Connect Snowflake [IN_PROGRESS]   ← crashed here
    ○  step_3: Configure [PENDING]
    ○  step_4: Watch the Loop [PENDING]
========================================================
```

### check-stale — gate check caching (exit 0 = cached, exit 1 = re-check)

```bash
# Use manifest cache if step N is COMPLETE and fresh; otherwise run API call
python3 "$MANIFEST_OPS" check-stale \
  --manifest "$MANIFEST" \
  --step     step_1 \
  || gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
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
