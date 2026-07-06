# Scaffold — GitLab

The GitLab scaffold skill sets up an Agentic DevOps pipeline with Snowflake CoCo
on GitLab CI in one guided conversation.

## What gets created

- A GitLab project from the [gitlab-coco-agent](https://gitlab.com/snowflake-dev/gitlab-coco-agent) template
- Three Snowflake objects (role, warehouse, SERVICE user) with OIDC trust
- Six GitLab CI/CD variables including `COCO_MAX_AUTO`
- Branch protection (push restricted, MR required)
- `.gitlab/coco-config.yml` with `conservative` fix ceiling

## Authentication

The skill requires `glab auth login` before any step. This is a hard gate — the skill
stops if `glab auth status` does not confirm an active session.

For the CI pipeline bot token (`GITLAB_TOKEN_COCO`), the skill offers two paths:

- **Use glab auth token** — convenient for development; pipeline loses access if you log out
- **Use a dedicated PAT** — recommended for long-lived or shared projects (`api + write_repository` scopes)

The CI pipeline uses two GitLab CI components from `snowflake-dev/snowflake-cicd-component`:
`configure-snowflake-cli` (OIDC + snow CLI) and `configure-cortex-code` (Cortex Code CLI + `connections.toml`).
Both use `template-only: true` so jobs extend them via `extends:`.

## The 6 steps

### Step 1 — Create Project

Asks: setup mode, project type (new / import), project path, visibility, Snowflake prefix and account.

For a new project: creates blank project, clones template, strips history, pushes clean commit.
For an existing project: clones and merges CoCo CI jobs into `.gitlab-ci.yml`.

### Step 2 — Hold Before Go-Live

Confirms `builds_access_level = disabled`. For existing projects, disables now.

### Step 3 — Connect Snowflake

Provisions the OIDC SERVICE user:

```sql
ALTER USER $SF_USER SET WORKLOAD_IDENTITY = (
  TYPE    = OIDC
  ISSUER  = 'https://gitlab.com'
  SUBJECT = 'project_path:$PROJECT_PATH:ref_type:branch:ref:main'
);
```

### Step 4 — Configure

Sets 6 CI/CD variables. The bot token is collected here (deferred from upfront questions).

**Quick start:** after variables are set, re-enables pipelines and applies branch protection. Done.

**Full setup:** asks whether to run the smoke test (Step 5).

### Step 5 — Watch the Loop (full setup)

Same smoke test as GitHub — scan-code job fires, issues and MRs appear automatically.

### Step 6 — Clean Up

Disable pipelines — drop Snowflake objects — delete project — remove local clone.
