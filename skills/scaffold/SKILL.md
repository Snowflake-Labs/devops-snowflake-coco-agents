---
name: scaffold
description: >
  Guided walkthrough for scaffolding a CoCo agent project on GitHub Actions
  or GitLab CI, provisioning Snowflake OIDC resources, and running the
  scan->issue->fix automation loop end-to-end.
  Use when: "scaffold a project", "scaffold from template", "set up coco agent",
  "scaffold github", "scaffold gitlab", "set up CI/CD automation",
  "automate scan-fix loop", "set up github-coco-agent", "set up gitlab-coco-agent".
---

## When to Load

Load when the user wants to scaffold a new CoCo agent project from a template,
set up the Snowflake OIDC integration, or run the scan->issue->fix automation loop.

## Routing Table

| Intent | Triggers | Action |
|---|---|---|
| GitHub | "github", "gh", "Actions", "GitHub" | Load `skills/scaffold/github/SKILL.md` |
| GitLab | "gitlab", "glab", "CI", "GitLab" | Load `skills/scaffold/gitlab/SKILL.md` |

If the platform is not clear from context, ask first:

```
ask_user_question:
  header: "Platform"
  question: "Which platform do you want to set up?"
  options:
    - label: "GitHub"
      description: "GitHub Actions + snowflake-cli-action (https://github.com/Snowflake-Labs/github-coco-agent)"
    - label: "GitLab"
      description: "GitLab CI + snowflake-cicd-component (https://gitlab.com/snowflake-dev/gitlab-coco-agent)"
```

Then load the chosen sub-skill.

## Shorthand Invocations

```
$devops-coco-agents:scaffold              → ask platform, load sub-skill
$devops-coco-agents:scaffold-for-github   → load skills/scaffold/github/SKILL.md directly
$devops-coco-agents:scaffold-for-gitlab   → load skills/scaffold/gitlab/SKILL.md directly
```

## What This Skill Does

```
prereq checks (gh/glab auth + snow connection test)
    └── Beat 1: scaffold repo/project from template
    └── Beat 2: disable Actions/pipelines until setup is complete
    └── Beat 3: snow sql setup.sql + DESC USER verify
    └── Beat 4: set GitHub secrets / GitLab CI/CD variables
    └── Beat 5 (optional): copy demo templates + enable CI + push → watch scan/fix loop
    └── Beat 6 (optional): teardown Snowflake resources + delete repo/project
```

## Prerequisites

- `gh` authenticated (`gh auth status`)
- `glab` authenticated (`glab auth status`)
- `snow` CLI configured with a connection that has ACCOUNTADMIN privileges
- `cortex` on PATH (set by `.envrc` via direnv in this workspace)
