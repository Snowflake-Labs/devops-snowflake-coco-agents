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
| GitHub | "github", "gh", "Actions", "GitHub" | Load `scaffold/github/SKILL.md` |
| GitLab | "gitlab", "glab", "CI", "GitLab" | Load `scaffold/gitlab/SKILL.md` |

If the platform is not clear from context, ask first:

```
ask_user_question:
  header: "Platform"
  question: "Which platform do you want to set up?"
  options:
    - label: "GitHub"
      description: "GitHub Actions + snowflake-cli-action (https://github.com/Snowflake-Labs/github-coco-agent)"
    - label: "GitLab"
      description: "GitLab CI + snowflake-cicd-component (https://gitlab.com/kameshsampath/gitlab-coco-agent)"
```

Then load the chosen sub-skill.

## Shorthand Invocations

```
$scaffold              → ask platform, load sub-skill
$scaffold github       → load .cortex/skills/scaffold/github/SKILL.md directly
$scaffold gitlab       → load .cortex/skills/scaffold/gitlab/SKILL.md directly
```

## What This Skill Does

```
cortex skill guides you through:
    ├── gh/glab repo create --template <https://github.com/...>
    ├── snow sql setup.sql   (provisions Snowflake OIDC resources)
    ├── gh secret set / glab variable set
    └── trigger first scan pipeline
            └── scan finds bugs → opens [coco-agent] issues
                    └── fix pipeline auto-fixes each → opens PR/MR
```

## Prerequisites

- `gh` authenticated (`gh auth status`)
- `glab` authenticated (`glab auth status`)
- `snow` CLI configured with a connection that has ACCOUNTADMIN privileges
- `cortex` on PATH (set by `.envrc` via direnv in this workspace)
