# Step 1c: Import Existing GitHub Repo

> Sub-step of Step 1 — Path A (`IMPORT_MODE = true`).

```bash
python3 "$MANIFEST_OPS" step-start --manifest ".coco-agent/$REPO_NAME/manifest.toml" --step step_1
gh repo clone "$REPO_PATH" "$REPO_NAME"
git clone --filter=blob:none --sparse \
  https://github.com/Snowflake-Labs/github-coco-agent /tmp/coco-tpl-$$
git -C /tmp/coco-tpl-$$ sparse-checkout set .github/workflows .cortex/prompts .github/coco-config.yml .github/secret_scanning.yml
mkdir -p "$REPO_NAME/.github/workflows" "$REPO_NAME/.cortex/prompts"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-scan.yml "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-fix.yml  "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.github/workflows/cortex-comment-fix.yml "$REPO_NAME/.github/workflows/"
cp /tmp/coco-tpl-$$/.cortex/prompts/scan.md "$REPO_NAME/.cortex/prompts/"
cp /tmp/coco-tpl-$$/.cortex/prompts/fix.md  "$REPO_NAME/.cortex/prompts/"
cp /tmp/coco-tpl-$$/.github/coco-config.yml "$REPO_NAME/.github/coco-config.yml"
cp /tmp/coco-tpl-$$/.github/secret_scanning.yml "$REPO_NAME/.github/secret_scanning.yml"
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
  .github/workflows/cortex-fix.yml .github/workflows/cortex-comment-fix.yml \
  .github/coco-config.yml .github/secret_scanning.yml \
  .cortex/ .coco-agent/
git -C "$REPO_NAME" commit -m "ci: add CoCo scan+fix workflows, prompts, config, and manifest [skip ci]"
git -C "$REPO_NAME" push

# Disable Actions — prevents workflows firing before secrets are configured
gh api "repos/$REPO_PATH/actions/permissions" -X PUT --input - <<<'{"enabled": false}'

python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_1
```

### What we did

- Cloned `$REPO_PATH` into `./$REPO_NAME`
- Copied workflows: `cortex-scan.yml`, `cortex-fix.yml`, `cortex-comment-fix.yml`
- Copied prompts: `scan.md`, `fix.md`
- Copied config: `.github/coco-config.yml`, `.github/secret_scanning.yml`
- Actions disabled — re-enabled in Step 4 (configure) just before go-live
