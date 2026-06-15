# devops-coco-agents

**Snowflake-native AI agents for Agentic DevOps.**

Scaffold an autonomous scan→issue→fix pipeline on GitHub Actions or GitLab CI in under 20 minutes. No stored secrets. No manual provisioning. One conversation.

<div class="grid cards" markdown>

-   :material-rocket-launch: **Scaffold in minutes**

    Guided 6-step setup — repo creation, Snowflake OIDC provisioning, CI secrets, optional smoke test.
    [Get started →](getting-started.md)

-   :material-brain: **Agentic DevOps**

    The first CI/CD skill that scores each finding and decides per-issue whether to auto-fix or escalate to a human.
    [How it works →](smart-fix/overview.md)

-   :material-snowflake: **Snowflake-native**

    OIDC auth via Workload Identity Federation. Your code analysis stays inside your Snowflake account.
    [Architecture →](scaffold/overview.md)

-   :material-code-tags: **IDD-structured**

    Intent Compression Ratio 48. One `/scaffold` instruction runs 48 distinct state-changing operations.
    [IDD and ICR →](idd/overview.md)

</div>

---

## What CoCo provisions in a single conversation

| Step | What happens | Who does the work |
|------|-------------|------------------|
| 1 | GitHub / GitLab repo created from hardened template | CoCo |
| 2 | Snowflake SERVICE user, role, and warehouse provisioned | CoCo |
| 3 | OIDC trust configured — zero long-lived secrets | CoCo |
| 4 | CI secrets and fix-mode policy pushed | CoCo |
| 5 | Optional: self-hosted runner installed and started | CoCo |
| 6 | Smoke test pushed — agent finds bugs, opens issues, raises PRs | CoCo |

## Install

```bash
cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
```

Then type in the CoCo chat panel:

```text
/scaffold-for-github   # GitHub Actions
/scaffold-for-gitlab   # GitLab CI
```

## Prerequisites

- [`gh`](https://cli.github.com) authenticated (`gh auth login`) — GitHub path
- [`glab`](https://gitlab.com/gitlab-org/cli) authenticated (`glab auth login`) — GitLab path
- [`snow`](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) CLI connected to Snowflake
- Python 3.11+
