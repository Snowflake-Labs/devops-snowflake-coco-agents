# Agentic DevOps with Snowflake CoCo

> Scaffold an autonomous scan-issue-fix pipeline on GitHub Actions or GitLab CI
> in one CoCo conversation. No stored secrets. No manual provisioning.
> **ICR 48** — one instruction, 48 distinct state-changing operations.

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

> [!TIP]
> New to CoCo? Start with `scaffold for agentic devops with GitHub` and the agent handles everything.

---

## Smart fix mode

Most tools treat every finding the same: auto-fix everything, or do nothing.
CoCo scores each finding before acting and documents the decision in the issue body:

> **Severity:** HIGH | **Complexity:** LOW | **Confidence:** HIGH | **Fix mode:** auto

### Decision matrix

| Ceiling | Severity | Complexity | Confidence | Action |
|---------|----------|------------|------------|--------|
| `conservative` | LOW | LOW | HIGH | auto-fix |
| `conservative` | LOW | LOW | MEDIUM | needs-review |
| `conservative` | MEDIUM+ | any | any | needs-review |
| `conservative` | any | MEDIUM+ | any | needs-review |
| `aggressive` | any | any | MEDIUM+ | auto-fix |
| `aggressive` | any | any | LOW | needs-review |
| `off` | any | any | any | needs-review |

### Config

The team controls the fix ceiling via config-as-code:

```yaml
# .github/coco-config.yml
coco_max_auto: conservative   # off | conservative | aggressive
```

> [!IMPORTANT]
> Change it in a PR -- the git history is your audit trail. A `COCO_MAX_AUTO`
> CI/CD variable overrides the file at runtime for experiments without touching code.

---

## What CoCo provisions

> [!NOTE]
> Zero long-lived secrets. All authentication uses Snowflake OIDC / Workload Identity Federation.

- GitHub / GitLab repo from a hardened template, clean single-commit history
- Snowflake SERVICE user, role, and warehouse with OIDC / Workload Identity Federation
- CI secrets and fix-mode policy committed to the repo
- Branch protection requiring at least one PR review before merge

---

## Prerequisites

> [!WARNING]
> Both `gh`/`glab` and `snow` must be authenticated before running the scaffold.

- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) -- the agentic IDE this plugin runs inside
- [`gh`](https://cli.github.com) authenticated (`gh auth login`) -- GitHub path
- [`glab`](https://gitlab.com/gitlab-org/cli) authenticated (`glab auth login`) -- GitLab path
- [`snow`](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) CLI connected to Snowflake
- Python 3.11+

---

## Documentation

Documentation source lives in `docs/`. Preview locally:

```bash
task docs:serve   # http://localhost:8000
```

| Section | |
|---------|-|
| [Getting Started](docs/getting-started.md) | Install, prerequisites, first scaffold |
| [Scaffold — GitHub](docs/scaffold/github.md) | GitHub Actions 6-step guide |
| [Scaffold — GitLab](docs/scaffold/gitlab.md) | GitLab CI 6-step guide |
| [Smart Fix](docs/smart-fix/overview.md) | Per-issue scoring, config ceiling, `/coco fix` trigger |
| [IDD and ICR](docs/idd/overview.md) | Intent-Driven Development, ICR 48 |
| [Demo walkthrough](docs/demo/github.md) | Step-by-step with expected outputs |

---

## Templates

| Platform | Template | Auth |
|----------|----------|------|
| GitHub Actions | [Snowflake-Labs/github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) | OIDC via [snowflake-cli-action](https://github.com/snowflakedb/snowflake-cli-action) |
| GitLab CI | [snowflake-dev/gitlab-coco-agent](https://gitlab.com/snowflake-dev/gitlab-coco-agent) | OIDC via [snowflake-cicd-component](https://gitlab.com/snowflake-dev/snowflake-cicd-component) |

---

## Testing (Eval Suite)

Determinism of the smoke-test demo generation is validated with an eval suite
in `evals/`. Two tasks run 5 attempts each to measure the pass rate of the
generation prompt:

| Task | What it checks |
|---|---|
| `smoke-test-de` | DE (Snowpark ETL) app: 1 auto-fix + ≥2 needs-review, SQL injection + subprocess present |
| `smoke-test-streamlit` | Streamlit app: same routing constraints |

A reliable prompt scores **5/5** (100%). Below 5/5 means the generation prompt
needs iteration.

### Running locally

```bash
cd evals
cp .env.example .env
# Edit .env: SNOWFLAKE_CONNECTION_NAME=<your-connection-name>

uv sync

# Sanity check — 1 attempt on DE only, fast
cortex-eval run --config config-single.yaml

# Full determinism suite — both tasks × 5 attempts
cortex-eval run --config config.yaml
```

Results are written to `evals/jobs/`.

### Iterating on the prompt

When a task fails, update `evals/scaffold/smoke-test-de/instruction.md` or
`evals/scaffold/smoke-test-streamlit/instruction.md` and re-run until you hit 5/5.
The accepted prompt then gets copied to
`skills/scaffold/shared/generate-demo.md`.

---

## Contributing

Commits must follow [conventional commit](https://www.conventionalcommits.org/) format.
Use `[skip-release]` in the commit message to bypass the auto-tag workflow on
maintenance commits.

```bash
task install        # install dev + docs deps via uv
pre-commit install  # wire hooks
task docs:serve     # preview docs at http://localhost:8000
# brew install bats-core
bats tests/         # run hook guard tests
```

Pre-commit hooks enforce: `check-yaml`, `markdownlint`, skill guidelines, ruff lint/format.
Step files under `skills/scaffold/*/steps/` must be 80 lines or fewer.

---

## License

[Apache 2.0](LICENSE)
