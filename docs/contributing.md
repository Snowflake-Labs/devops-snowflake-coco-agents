# Contributing

## Conventional commits

All commits must follow the conventional commit format. The `validate.yml` workflow
checks this on every PR.

```
type(scope): short description

Closes #N, closes #M
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`

Scopes: `scaffold`, `scaffold/github`, `scaffold/gitlab`, `dev`, `templates`

Skip the auto-tag workflow for maintenance commits:
```
[skip-release] chore: update lockfile
```

## Pre-commit hooks

```bash
task install       # install dev + docs deps
pre-commit install # wire hooks
```

Hooks run on every `git commit`:

- `trim-trailing-whitespace`, `end-of-file-fixer`, `check-merge-conflicts`
- `check-yaml`, `yamllint`
- `markdownlint`
- `Skill guidelines` — line count + no inline SKILL_DIR blocks
- `Skill LLM audit` — only runs when `skills/scaffold/*.md` files are staged
- `ruff` lint + format

## Step file limits

All step files under `skills/scaffold/*/steps/` must be **≤ 80 lines**.

Larger steps use a router + sub-step pattern:
- Router file (`step-N.md`) loads sub-steps
- Sub-step files (`step-Na.md`, `step-Nb.md`) contain the content

Run the checker manually:
```bash
python3 scripts/check_skill_guidelines.py
```

## Local docs preview

```bash
task docs:serve
```

Opens `http://localhost:8000` with live reload.

## Docs build + deploy

```bash
task docs:build    # build to site/
task docs:deploy   # push to gh-pages branch
```

GitHub Actions runs `deploy-docs.yml` automatically on pushes to `main` that touch `docs/**` or `mkdocs.yml`.
