# Config Reference

## `.github/coco-config.yml` (GitHub) / `.gitlab/coco-config.yml` (GitLab)

Ships in the template with a safe `conservative` default. Change via PR for a full audit trail.

```yaml
# Change via PR — the commit history is your governance record
# vars.COCO_MAX_AUTO overrides this value for runtime experiments
fix_mode:
  max_auto: conservative  # aggressive | conservative | off
  # aggressive:   auto-fix when AI confidence is medium or high
  # conservative: auto-fix only when severity=low, complexity=low, confidence=high  (default)
  # off:          never auto-fix — always require @coco fix comment
```

## Runtime override: `vars.COCO_MAX_AUTO`

Set in GitHub Actions repository variables (Settings → Secrets and variables → Actions → Variables)
or as a GitLab CI/CD variable (non-masked).

The variable takes priority over the config file. Use it to run experiments without committing a policy change:

```bash
# GitHub — set via CLI
gh variable set COCO_MAX_AUTO --repo "$REPO_PATH" --body "aggressive"

# GitLab — set via API
glab api "projects/$ENCODED_PATH/variables" --method PUT \
  -F "key=COCO_MAX_AUTO" -F "value=aggressive"
```

Remove the variable to revert to the config file value.

## Resolution order

```
1. vars.COCO_MAX_AUTO        ← runtime experiment
2. .github/coco-config.yml   ← config-as-code default
3. Built-in: "conservative"
```

## Audit log

Every scan run logs the active ceiling and source to the Actions/pipeline summary:

```
::notice::Fix ceiling: aggressive (source: vars.COCO_MAX_AUTO override)
::notice::Fix ceiling: conservative (source: .github/coco-config.yml)
```

!!! tip "Governance tip"
    Keep `max_auto: conservative` in the config file permanently.
    Use `vars.COCO_MAX_AUTO` only for time-boxed experiments.
    When the experiment ends, delete the variable — policy reverts to the reviewed default.
