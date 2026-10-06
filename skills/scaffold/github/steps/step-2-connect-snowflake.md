# Step 3: Connect Snowflake (Router)

> Part of the GitHub scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).

```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

**Gate check (staleness-aware):**

```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_1 \
  || gh api "repos/$REPO_PATH/actions/permissions" --jq .enabled
```

If `true`: ⚠️ Actions still enabled. Check Step 1 completed successfully.

---

**OIDC subject:** load `references/github-oidc-subject.md` and run it to the end. It reads
the subject this repo emits (immutable `repo:<owner>@<owner_id>/<repo>@<repo_id>:...` for
repos created after 2026-07-15), asks the user to accept or edit it, and sets `$OIDC_SUBJECT`.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll create**

| Object | Value |
|--------|-------|
| Role | `${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_ROLE` |
| Warehouse | `${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_USER` (TYPE = SERVICE) |
| Auth | OIDC, subject = `$OIDC_SUBJECT` |

Call `exit_plan_mode`. Then load `github/steps/step-2a-snowflake.md`.
