# Token Scopes

## GitHub

`gh auth login` (OAuth) covers all scaffold operations. No additional
configuration is needed for the `GITHUB_TOKEN` used by Actions workflows —
GitHub provisions it automatically.

If using a PAT instead of `gh auth login`, create one with `repo` scope:
`https://github.com/settings/tokens/new?scopes=repo`

---

## GitLab

### `GITLAB_TOKEN_COCO` — bot token set as CI/CD variable

Follows the official GitLab Duo Agent Platform convention `GITLAB_TOKEN_<integration>`.

| Scope | Why required |
|-------|-------------|
| `api` | Create/update CI/CD variables, create issues, post issue notes via REST API |
| `write_repository` | Push branches for fix MRs |
| `ai_features` | GitLab Duo Agent Platform integration — required for `@coco-agent` triggered pipelines to receive task context |

Create a Project Access Token at:
`https://gitlab.com/<group>/<project>/-/settings/access_tokens`

Or use the direct URL (pre-fills name and scopes):
`https://gitlab.com/-/user_settings/personal_access_tokens?name=coco-bot&scopes=api,write_repository,ai_features`

### `glab auth login` session token

Used by the scaffold skill for CLI operations (create project, disable pipelines, set variables).
Scope: `api` — granted automatically by the `glab` OAuth flow.

> Personal OAuth token — if you run `glab auth logout`, the pipeline loses
> access. For production use, create a dedicated Project Access Token above.

### Variables API restriction

The GitLab variables API (`/projects/:id/variables`) returns 403 when
`builds_access_level=disabled`. The scaffold skill temporarily sets
`builds_access_level=private` before writing variables and restores it to
`disabled` afterwards. This requires `curl -H "Authorization: Bearer <token>"`
— `glab api` does not forward the stored session token correctly for this
endpoint. See step-4a for the pattern.
