# Variables Reference

All CI/CD secrets and variables set by the scaffold skill.

## Snowflake secrets (set in Step 4a — both platforms)

| Variable | Type | Description |
|----------|------|-------------|
| `SNOWFLAKE_ACCOUNT` | Secret (masked) | Snowflake account identifier, e.g. `xy12345.us-east-1` |
| `SNOWFLAKE_ROLE` | Secret | Service user role, e.g. `DEMO_GH_REPO_COCO_AGENT_ROLE` |
| `SNOWFLAKE_WAREHOUSE` | Secret | Service warehouse, e.g. `DEMO_GH_REPO_COCO_AGENT_WH` |
| `SNOWFLAKE_USER` | Secret | Service user, e.g. `DEMO_GH_REPO_COCO_AGENT_USER` |
| `SNOWFLAKE_PAT` | Secret (masked) | PAT for local runner only — removed after smoke test |

## GitLab-specific

| Variable | Type | Description |
|----------|------|-------------|
| `GITLAB_TOKEN_COCO` | Secret (masked) | Bot token for creating MRs and issues |

## Fix-mode variable (set in Step 4a — both platforms)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `COCO_MAX_AUTO` | Variable (not masked) | `conservative` | Fix ceiling. Override without a PR for experiments. |

Values: `off` \| `conservative` \| `aggressive`

## GitHub-only

| Variable | Type | Description |
|----------|------|-------------|
| `SNOWFLAKE_TOKEN` | Env (injected by `snowflake-cli-action`) | OIDC token from Workload Identity Federation — ephemeral, not stored |

## Resolution for `COCO_MAX_AUTO`

```text
1. vars.COCO_MAX_AUTO        ← GitHub Actions repo variable / GitLab CI variable
2. .github/coco-config.yml   ← config-as-code default
3. Built-in: "conservative"
```
