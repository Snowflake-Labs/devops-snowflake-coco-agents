# Run Mode & Project Name Reference

Loaded by scaffold sub-skills before collecting any inputs.
Provides: (1) run-mode selection, (2) Mode Behaviour Reference, (3) petname generator.

---

## Mode Behaviour Reference

`$SKILL_MODE` is set here and controls one thing per beat:

- **guided** — show "Why this matters" before each plan preview (default)
- **standard** — skip "Why this matters"; show plan preview and confirm as normal

Beat-by-beat confirm gates fire in both modes.
Beat 6 teardown always shows a final confirm regardless of mode.
"What we did" is always shown in both modes.

---

## Step A — Ask run mode

```
ask_user_question:
  header: "Run mode"
  question: "How would you like to run the scaffold?"
  defaultAnswer: "Guided — explanations + beat-by-beat confirm"
  options:
    - label: "Guided — explanations + beat-by-beat confirm"
      description: "Explains each concept before acting. Good for first-timers."
    - label: "Standard — beat-by-beat confirm, skip explanations"
      description: "Shows what will happen and asks before each beat."
```

Set `$SKILL_MODE = guided` or `$SKILL_MODE = standard` from the answer.

---

## Step B — Generate project/repo name suggestion

You are a techy petname generator for a git repository. Generate a name using
the pattern `<adjective>-<noun>` where:

- **adjective** — personality adjective: fuzzy, blazing, sleepy, eager, cranky,
  atomic, humble, jolly, bold, wired, quirky, brave, nimble, swift
- **noun** — technical term: daemon, webhook, pipeline, cron, lambda, socket,
  cache, pod, flux, heap, stack, diff, patch, runner, sidecar, proxy, relay,
  shard, broker

Examples: `blazing-daemon`, `fuzzy-lambda`, `sleepy-sidecar`, `bold-webhook`,
`nimble-broker`, `quirky-shard`.

Use `<detected-username>/<generated-petname>` as the `defaultValue` for the
project/repo name question that follows in the calling skill.
