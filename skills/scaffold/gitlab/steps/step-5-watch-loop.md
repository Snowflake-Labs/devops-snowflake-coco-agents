# Step 5: Watch the Loop (Router)

> Part of the GitLab scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$PROJECT_NAME/.coco-agent/manifest.toml"
```

**Load in order:**

1. `gitlab/steps/step-5a-smoke.md` — Enable pipelines, push smoke test, watch loop
2. `gitlab/steps/step-5b-revert.md` — Revert, protect main, revoke PAT
