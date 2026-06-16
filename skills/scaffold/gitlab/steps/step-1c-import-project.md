# Step 1c: Import Existing GitLab Project

> Sub-step of Step 1 — Path A (`IMPORT_MODE = true`).

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$PROJECT_NAME/manifest.toml" --step step_1
glab repo clone "$PROJECT_PATH" "$PROJECT_NAME"
git clone --filter=blob:none --sparse \
  https://gitlab.com/snowflake-dev/gitlab-coco-agent /tmp/coco-tpl-$$
git -C /tmp/coco-tpl-$$ sparse-checkout set .cortex/prompts
mkdir -p "$PROJECT_NAME/.cortex/prompts"
cp /tmp/coco-tpl-$$/.cortex/prompts/scan.md "$PROJECT_NAME/.cortex/prompts/"
cp /tmp/coco-tpl-$$/.cortex/prompts/fix.md  "$PROJECT_NAME/.cortex/prompts/"
if [ -f "$PROJECT_NAME/.gitlab-ci.yml" ]; then
  echo "" >> "$PROJECT_NAME/.gitlab-ci.yml"
  tail -n +10 /tmp/coco-tpl-$$/.gitlab-ci.yml >> "$PROJECT_NAME/.gitlab-ci.yml"
  echo "⚠️ Merged CoCo jobs into existing .gitlab-ci.yml — review for conflicts"
else
  cp /tmp/coco-tpl-$$/.gitlab-ci.yml "$PROJECT_NAME/.gitlab-ci.yml"
fi
rm -rf /tmp/coco-tpl-$$
PROJECT_URL="https://gitlab.com/$PROJECT_PATH"
python3 "$MANIFEST_OPS" init \
  --draft-path ".coco-agent/$PROJECT_NAME" --prefix "$PREFIX" --repo-name "$PROJECT_NAME" \
  --visibility "" --run-mode "$SKILL_MODE" --platform "gitlab" \
  --template-name "gitlab-coco-agent"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$PROJECT_NAME" --to "$PROJECT_NAME/.coco-agent" \
  --repo-path "$PROJECT_PATH" --repo-url "$PROJECT_URL" --repo-name "$PROJECT_NAME"
git -C "$PROJECT_NAME" add .cortex/ .gitlab-ci.yml .coco-agent/
git -C "$PROJECT_NAME" commit -m "ci: add CoCo scan+fix pipeline and manifest [skip ci]"
git -C "$PROJECT_NAME" push
```

> ⚠️ Note: Pipelines are NOT disabled — the existing project may have active CI.
> Step-2 will offer to disable pipelines temporarily during Snowflake setup.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did

- Cloned `$PROJECT_PATH` into `./$PROJECT_NAME`
- Copied/merged `.gitlab-ci.yml`, `scan.md`, `fix.md` from template
- Manifest initialized and committed
