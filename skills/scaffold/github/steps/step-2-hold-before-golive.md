# Step 2: Hold Before Go-Live

> Part of the GitHub scaffold skill. Load when executing Step 2.
> For SKILL_DIR resolution, see `references/manifest.md`.

```bash
SKILL_DIR=$(find ~/.snowflake/cortex/plugins -name "manifest_ops.py" \
  -path "*/devops-coco-agents/skills/scaffold/scripts/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname 2>/dev/null)
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/skills/scaffold"
MANIFEST_OPS="$SKILL_DIR/scripts/manifest_ops.py"
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

**Gate check (staleness-aware):**
```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_1 \
  || { gh api "repos/$REPO_PATH" --jq .name 2>&1 && ls "$REPO_NAME" 2>&1; }
```
If either fails:
> ⚠️ **Gate check failed:** Remote repo or local clone not found. Complete Step 1 first.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**Why this matters** (Guided mode only):
> Actions were disabled when the repo was created to prevent spurious
> workflow failures during setup. This step confirms that state before
> provisioning Snowflake resources.

**What we'll do**
```
Verifies: GitHub Actions disabled on $REPO_PATH (expected: enabled = false)
```

Call `exit_plan_mode`. Then execute directly:

```bash
python3 "$MANIFEST_OPS" step-start --manifest "$MANIFEST" --step step_2
gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```
Expected: `false`. If `true`, re-disable:
```bash
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_2
```

### What we did
- Confirmed GitHub Actions are disabled on `$REPO_PATH`
- No workflows will fire until Watch the Loop re-enables them
