# Commands Reference

All commands are invoked from the CoCo chat panel. Use the full plugin command
form (`$devops-coco-agents:<command>`) or describe your intent in natural language.

## Scaffold commands

| Command | Alias | What it does |
|---------|-------|--------------|
| `$devops-coco-agents:scaffold` | `/scaffold` | Choose platform interactively |
| `$devops-coco-agents:scaffold-for-github` | `/scaffold-for-github` | Guided GitHub Actions setup |
| `$devops-coco-agents:scaffold-for-gitlab` | `/scaffold-for-gitlab` | Guided GitLab CI setup |

## IDD commands

| Command | Alias | What it does |
|---------|-------|--------------|
| `$devops-coco-agents:idd` | `/idd` | Choose IDD tool interactively |
| `$devops-coco-agents:idd-evaluate-prompt` | `/idd-evaluate-prompt` | Score a prompt on IDD dimensions |
| `$devops-coco-agents:idd-rewrite-prompt` | `/idd-rewrite-prompt` | Guided IDD rewrite |
| `$devops-coco-agents:idd-measure-icr` | `/idd-measure-icr` | Measure Intent Compression Ratio |

## In-pipeline triggers

These are not skill commands — they run inside CI pipelines:

| Trigger | Platform | Effect |
|---------|----------|--------|
| Issue labeled `coco:auto-fix` | GitHub | Runs `cortex-fix.yml` automatically |
| Issue opened with `[coco-agent]` title | GitHub | Runs `cortex-fix.yml` (legacy path) |
| Comment `/coco fix` or `/coco-agent fix` | GitHub | Runs `cortex-comment-fix.yml` |
| Pipeline trigger with `AI_FLOW_TITLE =~ /\[coco-agent\]/` | GitLab | Runs `coco-agent` job |
| Comment `/coco-agent fix` | GitLab | Triggers via Duo Agent Platform |
