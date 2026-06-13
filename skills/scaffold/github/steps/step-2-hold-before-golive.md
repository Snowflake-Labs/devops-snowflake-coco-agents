# Step 2: Hold Before Go-Live

> Part of the GitHub scaffold skill. Load when executing Step 2.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
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
