# Agentic DevOps with Snowflake CoCo

**One conversation. Autonomous CI/CD that thinks before it acts.**

Scaffold a scan-issue-fix pipeline on GitHub Actions or GitLab CI in under 20 minutes. No stored secrets. No manual provisioning.

<div class="grid cards" markdown>

-   **Scaffold in minutes**

    Six guided steps: repo creation, Snowflake OIDC provisioning, CI secrets, branch protection, optional smoke test.
    [Get started](getting-started.md)

-   **Agentic DevOps**

    CoCo scores each finding and decides per-issue whether to auto-fix or escalate based on a team-configured policy.
    [How it works](smart-fix/overview.md)

-   **Snowflake-native**

    OIDC via Workload Identity Federation. No stored credentials. Your code analysis stays inside your Snowflake account boundary.
    [Architecture](scaffold/overview.md)

-   **IDD-structured**

    Intent Compression Ratio 48. One `$devops-coco-agents:scaffold` instruction runs 48 distinct state-changing operations.
    [IDD and ICR](idd/overview.md)

</div>

---

## What CoCo provisions in a single conversation

| Step | What happens | Who does the work |
|------|-------------|------------------|
| 1 | GitHub / GitLab repo created from hardened template | CoCo |
| 2 | Snowflake SERVICE user, role, and warehouse provisioned | CoCo |
| 3 | OIDC trust configured, zero long-lived secrets | CoCo |
| 4 | CI secrets and fix-mode policy pushed | CoCo |
| 5 | Optional: smoke test pushed — scan finds bugs, issues raised, fix PRs opened | CoCo |
| 6 | Smoke test pushed — agent finds bugs, opens issues, raises PRs | CoCo |

## Install

```bash
cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
```

Then in the CoCo chat panel, describe what you want:

```text
scaffold for agentic devops with GitHub
scaffold for agentic devops with GitLab
```

Or use the shorthand:

```text
$devops-coco-agents:scaffold-for-github   # GitHub Actions
$devops-coco-agents:scaffold-for-gitlab   # GitLab CI
```

## Prerequisites

- [`gh`](https://cli.github.com) authenticated (`gh auth login`) — GitHub path
- [`glab`](https://gitlab.com/gitlab-org/cli) authenticated (`glab auth login`) — GitLab path
- [`snow`](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) CLI connected to Snowflake
- Python 3.11+
