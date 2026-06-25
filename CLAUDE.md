# devops-coco-agents

Plugin for scaffolding CoCo agent projects on GitHub Actions or GitLab CI,
and for applying Intent-Driven Development (IDD) principles to prompts and workflows.

## Available Commands

### Scaffold

- `/scaffold`              — Choose platform and scaffold (GitHub or GitLab)
- `/scaffold-for-github`   — Scaffold a GitHub Actions CoCo agent project
- `/scaffold-for-gitlab`   — Scaffold a GitLab CI CoCo agent project

### IDD

- `/idd`                   — IDD audit, rewrite, or ICR measurement
- `/idd-evaluate-prompt`   — Audit a prompt for IDD alignment (Goal/Requirements/Constraints/Output)
- `/idd-rewrite-prompt`    — Rewrite a prompt using the IDD structure
- `/idd-measure-icr`       — Measure the Intent Compression Ratio of a workflow
