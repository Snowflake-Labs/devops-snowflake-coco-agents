# Step 1: Create Project (Router)

> Part of the GitHub scaffold skill.

Resolve `SKILL_DIR` and `MANIFEST_OPS` per `references/manifest.md` (## SKILL_DIR Resolution).
```bash
MANIFEST="$REPO_NAME/.coco-agent/manifest.toml"
```

Route based on `IMPORT_MODE` (set in coordinator SKILL.md from user's path choice):
- `IMPORT_MODE = true` → load `github/steps/step-1c-import-repo.md`
- `IMPORT_MODE = false` → load `github/steps/step-1b-create-repo.md`
