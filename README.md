# Agentic DevOps with Snowflake CoCo

> Scaffold an autonomous scan-issue-fix pipeline on GitHub Actions or GitLab CI
> in one CoCo conversation. No stored secrets. No manual provisioning.
> **ICR 48** — one instruction, 48 distinct state-changing operations.

[![Docs](https://img.shields.io/badge/docs-snowflake--labs.github.io-0074D9)](https://snowflake-labs.github.io/devops-snowflake-coco-agents/)

---

CoCo provisions a complete Agentic DevOps pipeline — repo, Snowflake OIDC trust,
CI secrets, branch protection — without a single manual step. The agent then scans
every push, opens issues, and decides per-finding whether to raise a fix PR or wait
for a human.

## Quick start

1. Install [Cortex Code (CoCo)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
2. Install the plugin:

   ```bash
   cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
   ```

3. In the CoCo chat panel, just describe what you want:

   ```text
   scaffold for agentic devops with GitHub
   scaffold for agentic devops with GitLab
   ```

   Or use the explicit plugin command:

   ```text
   $devops-coco-agents:scaffold-for-github   # GitHub Actions
   $devops-coco-agents:scaffold-for-gitlab   # GitLab CI
   ```

Done in under 10 minutes. The scaffold executes 48 state-changing operations so you don't have to.

---

## Smart fix mode

Most tools treat every finding the same: auto-fix everything, or do nothing.
CoCo scores each finding before acting and documents the decision in the issue body:

> **Severity:** HIGH | **Complexity:** LOW | **Confidence:** HIGH | **Fix mode:** auto

The team controls the fix ceiling via config-as-code:

```yaml
# .github/coco-config.yml
coco_max_auto: conservative   # off | conservative | aggressive
```

Change it in a PR — the git history is your audit trail. A `COCO_MAX_AUTO`
CI/CD variable overrides the file at runtime for experiments without touching code.

---

## What CoCo provisions

- GitHub / GitLab repo from a hardened template, clean single-commit history
- Snowflake SERVICE user, role, and warehouse with OIDC / Workload Identity Federation
- Zero long-lived secrets — no tokens stored in CI environment
- CI secrets and fix-mode policy committed to the repo
- Branch protection requiring at least one PR review before merge

---

## Prerequisites

- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) — the agentic IDE this plugin runs inside
- [`gh`](https://cli.github.com) authenticated (`gh auth login`) — GitHub path
- [`glab`](https://gitlab.com/gitlab-org/cli) authenticated (`glab auth login`) — GitLab path
- [`snow`](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) CLI connected to Snowflake
- Python 3.11+

---

## Documentation

Full docs at **[snowflake-labs.github.io/devops-snowflake-coco-agents](https://snowflake-labs.github.io/devops-snowflake-coco-agents/)**

| Section | |
|---------|-|
| [Getting Started](https://snowflake-labs.github.io/devops-snowflake-coco-agents/getting-started/) | Install, prerequisites, first scaffold |
| [Scaffold — GitHub](https://snowflake-labs.github.io/devops-snowflake-coco-agents/scaffold/github/) | GitHub Actions 6-step guide |
| [Scaffold — GitLab](https://snowflake-labs.github.io/devops-snowflake-coco-agents/scaffold/gitlab/) | GitLab CI 6-step guide |
| [Smart Fix](https://snowflake-labs.github.io/devops-snowflake-coco-agents/smart-fix/overview/) | Per-issue scoring, config ceiling, `/coco fix` trigger |
| [IDD and ICR](https://snowflake-labs.github.io/devops-snowflake-coco-agents/idd/overview/) | Intent-Driven Development, ICR 48 |
| [Demo walkthrough](https://snowflake-labs.github.io/devops-snowflake-coco-agents/demo/github/) | Step-by-step with expected outputs |

---

## Templates

| Platform | Template | Auth |
|----------|----------|------|
| GitHub Actions | [Snowflake-Labs/github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) | OIDC via [snowflake-cli-action](https://github.com/snowflakedb/snowflake-cli-action) |
| GitLab CI | [snowflake-dev/gitlab-coco-agent](https://gitlab.com/snowflake-dev/gitlab-coco-agent) | OIDC via [snowflake-cicd-component](https://gitlab.com/snowflake-dev/snowflake-cicd-component) |

---

## Contributing

Commits must follow [conventional commit](https://www.conventionalcommits.org/) format.
Use `[skip-release]` in the commit message to bypass the auto-tag workflow on
maintenance commits.

```bash
task install        # install dev + docs deps via uv
pre-commit install  # wire hooks
task docs:serve     # preview docs at http://localhost:8000
```

Pre-commit hooks enforce: `check-yaml`, `markdownlint`, skill guidelines, ruff lint/format.
Step files under `skills/scaffold/*/steps/` must be 80 lines or fewer.

---

## License

Plugin code: [Apache 2.0](LICENSE) · Skill content (`skills/`): [Snowflake Skills License](skills/scaffold/LICENSE)
