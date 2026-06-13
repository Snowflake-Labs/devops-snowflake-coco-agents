# Step 2: Hold Before Go-Live

> Part of the GitLab scaffold skill. Load when executing Step 2.
> For SKILL_DIR resolution, see `references/manifest.md`.

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

**Gate check (staleness-aware):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_1 \
  || { glab api "projects/$ENCODED_PATH" --jq .name 2>&1 && ls "$PROJECT_NAME" 2>&1; }
```
If either fails:
> ⚠️ **Gate check failed:** Remote project or local clone not found. Complete Step 1 first.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Pipelines were disabled when the project was created to prevent spurious
> job failures during setup. This step confirms that state before
> provisioning Snowflake resources.

**What we'll do**
```
Verifies: CI/CD pipelines disabled on $PROJECT_PATH (expected: builds_access_level = disabled)
```

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_2
glab api "projects/$ENCODED_PATH" --jq .builds_access_level
```
Expected: `"disabled"`. If not, re-disable:
```bash
glab api "projects/$ENCODED_PATH" -X PUT -F builds_access_level=disabled 2>&1
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_2
```

### What we did
- Confirmed CI/CD pipelines are disabled on `$PROJECT_PATH`
- No jobs will fire until Watch the Loop re-enables them
