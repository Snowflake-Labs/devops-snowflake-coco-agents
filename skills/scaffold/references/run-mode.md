# Run Mode & Project Name Reference

Loaded by scaffold sub-skills before collecting any inputs.
Provides: (1) run-mode selection, (2) Mode Behaviour Reference, (3) petname
generator, (4) Snowflake prefix detection, (5) Snowflake account detection.

---

## Mode Behaviour Reference

`$SKILL_MODE` is set here and controls one thing per step:

- **guided** — show "Why this matters" before each plan preview (default)
- **standard** — skip "Why this matters"; show plan preview and confirm as normal

Step-by-step confirm gates fire in both modes.
Clean Up teardown always shows a final confirm regardless of mode.
"What we did" is always shown in both modes.

---

## Step A — Ask run mode

```
ask_user_question:
  header: "Run mode"
  question: "How would you like to run the scaffold?"
  defaultAnswer: "Guided — explanations + step-by-step confirm"
  options:
    - label: "Guided — explanations + step-by-step confirm"
      description: "Explains each concept before acting. Good for first-timers."
    - label: "Standard — step-by-step confirm, skip explanations"
      description: "Shows what will happen and asks before each step."
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

---

## Step C — Snowflake resource prefix

Detect the current Snowflake user and use it as the default prefix:

```bash
snow sql -q "SELECT CURRENT_USER()" --format json \
  | python3 -c "import sys,json; u=list(json.load(sys.stdin)[0].values())[0]; print(u.split('@')[0].upper()[:10])"
```

Then ask:

```
ask_user_question:
  header: "Prefix"
  question: "Snowflake resource prefix? All objects will be named PREFIX_*_COCO_AGENT_*"
  type: text
  defaultValue: "<detected-snowflake-user>"
```

Store as `$PREFIX`. The calling skill uses this to name the role, warehouse,
and WORKLOAD_IDENTITY user.

---

## Step D — Snowflake account

Check `$SNOWFLAKE_ACCOUNT` env var first. If already set, use it silently.
If unset, ask:

```
ask_user_question:
  header: "Account"
  question: "Snowflake account identifier? (e.g. xy12345.us-east-1)"
  type: text
  defaultValue: ""
```

Store as `$SNOWFLAKE_ACCOUNT`.
