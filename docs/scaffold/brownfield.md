# Brownfield — Adding CoCo to an Existing Repo

You don't need a new repo to use CoCo. The scaffold skill supports adding the
scan→issue→fix pipeline to any existing GitHub repo or GitLab project.

## How it works

When you choose **Add to existing repo/project** at the project type question,
the skill runs the import path (step-1c):

1. Clones the existing repo
2. Sparse-copies CI workflow files from the template (GitHub: `cortex-scan.yml`, `cortex-fix.yml`; GitLab: CoCo jobs appended to `.gitlab-ci.yml`)
3. Copies `.cortex/prompts/scan.md` and `fix.md`
4. Commits with `[skip ci]` — does not trigger existing workflows

## What changes in your repo

=== "GitHub"

    Files added:
    ```
    .github/workflows/cortex-scan.yml
    .github/workflows/cortex-fix.yml
    .github/workflows/cortex-comment-fix.yml
    .github/coco-config.yml
    .cortex/prompts/scan.md
    .cortex/prompts/fix.md
    .coco-agent/manifest.toml
    ```

=== "GitLab"

    Files added/modified:
    ```
    .gitlab-ci.yml          (CoCo jobs appended — review for conflicts)
    .gitlab/coco-config.yml
    .cortex/prompts/scan.md
    .cortex/prompts/fix.md
    .coco-agent/manifest.toml
    ```

## Branch protection

For existing repos that already have branch protection configured, the skill
**preserves existing rules** rather than overwriting them.

The detection logic:

=== "GitHub"

    ```bash
    EXISTING=$(gh api "repos/$REPO_PATH/branches/main/protection" 2>/dev/null)
    if [ -n "$EXISTING" ]; then
      echo "Existing branch protection found — keeping current rules."
    else
      # Apply CoCo default: require 1 PR review
    fi
    ```

=== "GitLab"

    ```bash
    EXISTING=$(glab api "projects/$ENCODED_PATH/protected_branches" | ...)
    # Apply CoCo protection only if main is not already protected
    ```

## `.gitlab-ci.yml` merge

If an existing `.gitlab-ci.yml` is present, the skill appends the CoCo jobs
rather than replacing the file. Review the result for duplicate stage definitions
or conflicting `default:` blocks before pushing.

!!! warning
    After the merge, check that `stages:` in `.gitlab-ci.yml` includes `scan` and `fix`.
    The CoCo jobs use these stage names.
