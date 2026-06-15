# Comment Trigger — `@coco fix`

Any issue labelled `coco:needs-review` can be triggered manually by commenting on it.
This works regardless of the `COCO_MAX_AUTO` ceiling — the human decision overrides the policy.

## GitHub

Comment on any issue (including `coco:needs-review` ones):

```text
@coco fix
```

or:

```text
@coco-agent fix
```

The `cortex-comment-fix.yml` workflow triggers, runs the same fix logic as the auto path,
and opens a PR on a new branch.

## GitLab

Comment on any issue:

```text
@coco-agent fix
```

The GitLab Duo Agent Platform detects the `@coco-agent` mention and sends a pipeline
trigger with the issue context. The `coco-agent` job picks it up and opens an MR.

## What happens after the trigger

1. CoCo reads the issue title and body
2. Applies the minimal correct fix from `.cortex/prompts/fix.md`
3. Commits to a new branch: `coco/fix-<run-id>`
4. Opens a PR/MR with the diff
5. Comments on the original issue: "CoCo completed the task. PR opened for review."

If no file changes are needed, the comment says "No file changes needed" and no PR is opened.

## When to use `@coco fix`

- The issue was labelled `coco:needs-review` (high complexity or low confidence) but you've reviewed it and want to proceed
- You want to re-trigger a fix after the first attempt missed something
- The ceiling is set to `off` and you want to override for a specific issue

!!! note
    `@coco fix` always runs the same fix logic regardless of scoring. If the issue
    was flagged as complex, CoCo will still apply the minimal fix described in the
    issue body — the human is authorising the attempt, not guaranteeing a clean result.
