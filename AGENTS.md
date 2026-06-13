# Agent & Contributor Conventions

This file documents conventions for both human contributors and AI agents
working in this repository.

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <short description>
```

Common types: `feat`, `fix`, `chore`, `docs`, `ci`, `refactor`

Examples:

- `feat(scaffold): add teardown sub-skill`
- `fix(gitlab): correct OIDC subject format`
- `ci: update yamllint pre-commit hook`

## Skill Development Standards

- Frontmatter: `name` and `description` fields only
- Keep each `SKILL.md` under 500 lines; move long reference content to `references/`
- Use `⚠️ MANDATORY` only for truly required stops — never `ALWAYS` or `NEVER`
- All user interactions must go through `ask_user_question`
- Collect all required inputs at Stopping Points before any action that creates resources
- Use `enter_plan_mode` + `exit_plan_mode` around each beat's confirmation (single confirm, not multiple raw asks)
- Three-point beat structure: "What I'll do" → execute → "What we did"

## Repo References

Always use full HTTPS URLs — never org/repo shorthand:

| Resource | URL |
|----------|-----|
| This plugin | `https://github.com/Snowflake-Labs/devops-snowflake-coco-agents` |
| GitHub template | `https://github.com/Snowflake-Labs/github-coco-agent` |
| GitLab template | `https://gitlab.com/kameshsampath/gitlab-coco-agent` |

## Plugin Names

- **GitHub repo name** (marketplace discoverability): `devops-snowflake-coco-agents`
- **Plugin `name` field** (post-install): `devops-coco-agents`
