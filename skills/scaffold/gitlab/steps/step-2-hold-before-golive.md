# Step 2: Hold Before Go-Live

> Part of the GitLab scaffold skill. Load when executing Step 2.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

**Gate check (staleness-aware):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_1 \
  || { glab api "projects/$ENCODED_PATH" | _j "['name']" 2>&1 && ls "$PROJECT_NAME" 2>&1; }
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
glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"
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
