# Manifest Reference

The scaffold skill tracks all provisioned resources in a TOML manifest at
`.coco-agent/manifest.toml` inside the scaffolded repo.

## Schema

```toml
[project]
repo_name      = "nimble-proxy"
repo_path      = "ksampath/nimble-proxy"
repo_url       = "https://github.com/ksampath/nimble-proxy"
visibility     = "private"
platform       = "github"      # or "gitlab"
template_name  = "github-coco-agent"
run_mode       = "guided"
prefix         = "DEMO"

[steps]
step_1 = "COMPLETE"
step_2 = "COMPLETE"
step_3 = "COMPLETE"
step_4 = "IN_PROGRESS"   # crashed mid-step — resume from start of step_4
step_5 = "NOT_STARTED"
step_6 = "NOT_STARTED"

[snowflake]
user      = "DEMO_GH_NIMBLE_PROXY_COCO_AGENT_USER"
role      = "DEMO_GH_NIMBLE_PROXY_COCO_AGENT_ROLE"
warehouse = "DEMO_GH_NIMBLE_PROXY_COCO_AGENT_WH"

[runner]
pid       = 12345
runner_id = ""

[snowflake.pat]
pat_name = ""   # populated if local runner was set up
```

## Step states

| State | Meaning |
|-------|---------|
| `NOT_STARTED` | Step has not begun |
| `IN_PROGRESS` | Step started but not completed — resume from start |
| `COMPLETE` | Step finished successfully |

## Manifest location

- **In-repo:** `.coco-agent/manifest.toml` (committed to the scaffolded repo)
- **Draft:** `.coco-agent/<repo-name>/manifest.toml` (before step-1 completes)

## Resume detection

On every invocation, the skill runs:

```bash
MANIFEST_IN_REPO=$(find . -maxdepth 2 -name "manifest.toml" -path "*/.coco-agent/*")
```

If found, it reads the prefix, repo name, and step states — and resumes from the first
non-complete step without re-asking any question already in the manifest.
