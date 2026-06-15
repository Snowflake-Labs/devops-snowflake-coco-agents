# devops-coco-agents

> **Agentic DevOps on Snowflake** — scaffold an autonomous scan→issue→fix pipeline
> on GitHub Actions or GitLab CI in one conversation.

[![Docs](https://img.shields.io/badge/docs-snowflake--labs.github.io-0074D9)](https://snowflake-labs.github.io/devops-snowflake-coco-agents/)

---

## What it does

The scaffold skill provisions a complete Agentic DevOps pipeline end-to-end:

- GitHub / GitLab repo from a hardened template (zero template history)
- Snowflake SERVICE user with OIDC / Workload Identity Federation — no stored secrets
- CI secrets and fix-mode policy configured and committed
- Branch protection applied

The scan→issue→fix loop runs automatically on every push. CoCo scores each finding
by severity, complexity, and confidence — and decides whether to auto-fix or
escalate to a human. The team controls the ceiling via `.github/coco-config.yml`,
reviewed in a PR, auditable in git history.

---

## Install

```bash
cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
```

## Usage

```text
/scaffold-for-github   # GitHub Actions
/scaffold-for-gitlab   # GitLab CI
/scaffold              # choose interactively
/idd                   # Intent-Driven Development tools
```

## Prerequisites

- [`gh`](https://cli.github.com) or [`glab`](https://gitlab.com/gitlab-org/cli) — authenticated
- [`snow`](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) — connected to Snowflake
- Python 3.11+

---

## Documentation

Full docs at **[snowflake-labs.github.io/devops-snowflake-coco-agents](https://snowflake-labs.github.io/devops-snowflake-coco-agents/)**

| Section | |
|---------|-|
| [Getting Started](https://snowflake-labs.github.io/devops-snowflake-coco-agents/getting-started/) | Install, prerequisites, first scaffold |
| [Scaffold — GitHub](https://snowflake-labs.github.io/devops-snowflake-coco-agents/scaffold/github/) | GitHub Actions 6-step guide |
| [Scaffold — GitLab](https://snowflake-labs.github.io/devops-snowflake-coco-agents/scaffold/gitlab/) | GitLab CI 6-step guide |
| [Smart Fix Mode](https://snowflake-labs.github.io/devops-snowflake-coco-agents/smart-fix/overview/) | Per-issue scoring, config-as-code ceiling, `@coco fix` |
| [IDD and ICR](https://snowflake-labs.github.io/devops-snowflake-coco-agents/idd/overview/) | Intent-Driven Development, ICR 48 |
| [Demo walkthrough](https://snowflake-labs.github.io/devops-snowflake-coco-agents/demo/github/) | Step-by-step with expected outputs |

---

## Templates

| Platform | Template | Auth |
|----------|----------|------|
| GitHub Actions | [Snowflake-Labs/github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) | OIDC via [snowflake-cli-action](https://github.com/snowflakedb/snowflake-cli-action) |
| GitLab CI | [kameshsampath/gitlab-coco-agent](https://gitlab.com/kameshsampath/gitlab-coco-agent) | OIDC via [snowflake-cicd-component](https://gitlab.com/snowflake-dev/snowflake-cicd-component) |

---

## Contributing

Commits must follow the [conventional commit](https://www.conventionalcommits.org/) format.
Use `[skip-release]` prefix to bypass the auto-tag workflow on maintenance commits.

```bash
task install       # install dev + docs deps via uv
pre-commit install  # wire hooks
task docs:serve    # preview docs at http://localhost:8000
```

Pre-commit hooks: `check-yaml`, `markdownlint`, skill guidelines, ruff lint/format.
Step files under `skills/scaffold/*/steps/` must be ≤ 80 lines.

---

## License

Plugin code: [Apache 2.0](LICENSE) · Skill content (`skills/`): [Snowflake Skills License](skills/scaffold/LICENSE)
