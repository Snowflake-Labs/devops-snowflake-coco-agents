# Step 3: Connect Snowflake (Router)

> Part of the GitLab scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).

```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

**Gate check (staleness-aware):**

```bash
python3 "$MANIFEST_OPS" check-stale --manifest "$MANIFEST" --step step_1 \
  || glab api "projects/$ENCODED_PATH" | _j "['builds_access_level']"
```

If not `"disabled"`: ⚠️ Pipelines still enabled. Check Step 1 completed successfully.

---

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll create**

| Object | Value |
|--------|-------|
| Role | `${PREFIX}_GL_${REPO_NAME_NORM}_COCO_AGENT_ROLE` |
| Warehouse | `${PREFIX}_GL_${REPO_NAME_NORM}_COCO_AGENT_WH` (XS, auto-suspend 60s) |
| User | `${PREFIX}_GL_${REPO_NAME_NORM}_COCO_AGENT_USER` (TYPE = SERVICE) |
| Auth | OIDC, subject = `project_path:$PROJECT_PATH:ref_type:branch:ref:main` |

Call `exit_plan_mode`. Then load `gitlab/steps/step-3a-snowflake.md`.
