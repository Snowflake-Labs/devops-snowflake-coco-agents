# Step 1c: Import Existing GitHub Repo

> Sub-step of Step 1 — Path A (`IMPORT_MODE = true`).

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$REPO_NAME/manifest.toml" --step step_1
gh repo clone "$REPO_PATH" "$REPO_NAME"
git clone --filter=blob:none --sparse \
  https://github.com/Snowflake-Labs/github-coco-agent /tmp/coco-tpl-$$
git -C /tmp/coco-tpl-$$ sparse-checkout set .github/workflows .cortex/prompts
mkdir -p "$REPO_NAME/.github/workflows" "$REPO_NAME/.cortex/prompts"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-scan.yml "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-fix.yml  "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.cortex/prompts/scan.md "$REPO_NAME/.cortex/prompts/"
cp /tmp/coco-tpl-$$/.cortex/prompts/fix.md  "$REPO_NAME/.cortex/prompts/"
rm -rf /tmp/coco-tpl-$$
REPO_URL=$(gh repo view "$REPO_PATH" --json url -q .url)
python3 "$MANIFEST_OPS" init \
  --draft-path ".coco-agent/$REPO_NAME" --prefix "$PREFIX" --repo-name "$REPO_NAME" \
  --visibility "" --run-mode "$SKILL_MODE" --platform "github" \
  --template-name "github-coco-agent"
python3 "$MANIFEST_OPS" move \
  --from ".coco-agent/$REPO_NAME" --to "$REPO_NAME/.coco-agent" \
  --repo-path "$REPO_PATH" --repo-url "$REPO_URL"
git -C "$REPO_NAME" add .github/workflows/cortex-scan.yml \
  .github/workflows/cortex-fix.yml .cortex/ .coco-agent/
git -C "$REPO_NAME" commit -m "ci: add CoCo scan+fix workflow and manifest [skip ci]"
git -C "$REPO_NAME" push
```

> ⚠️ Note: Actions are NOT disabled — the existing repo may have active CI.
> Step-2 will offer to disable Actions temporarily during Snowflake setup.

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did
- Cloned `$REPO_PATH` into `./$REPO_NAME`
- Copied `cortex-scan.yml`, `cortex-fix.yml`, `scan.md`, `fix.md` from template
- Manifest initialized and committed
