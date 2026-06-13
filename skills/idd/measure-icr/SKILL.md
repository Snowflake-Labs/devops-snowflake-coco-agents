---
name: idd/measure-icr
description: >
  Calculate the Intent Compression Ratio (ICR) for a workflow, script, or
  CI/CD pipeline. Counts total operations vs intent expressions and classifies
  the result. Recommends what to compress next to increase agentic readiness.
  Use when: "measure ICR", "calculate ICR", "what is ICR of this workflow",
  "how much compression", "intent compression ratio".
---

## ICR Reference

```
ICR = Total Required Operations (Ops) / Intent Expressions

1 intent : N ops
```

| ICR Range | Classification | Agentic Readiness |
|---|---|---|
| 1–3 | Command relay | Low — agent is just a wrapper |
| 4–8 | Automation wrapper | Medium — meaningful compression |
| 9–15 | Architectural partner | High — strong agentic readiness |
| 15+ | Intent engine | Very high — system owns the DAG |

**Glass Box principle:** ICR alone is not the goal. Target: high ICR + full
observability + safe retry = Glass Box Compression.

---

## Stopping Points

Ask the user to provide the workflow:

```
ask_user_question:
  header: "Workflow"
  question: "Paste your workflow, script, Taskfile, CI config, or describe the steps you want to measure."
  type: text
  defaultValue: ""
```

Optionally ask for context:
```
ask_user_question:
  header: "Intent count"
  question: "How many natural language intent expressions does the user write to trigger this? (e.g. 1 for a single $scaffold invocation)"
  type: text
  defaultValue: "1"
```

---

## Analysis

**Step 1 — Count Operations (Ops)**

Walk through the workflow and count each distinct state-changing step:
- Every API call / CLI command that creates, modifies, or deletes state
- Every validation / verification step
- Every credential or secret operation
- Every git operation

Do NOT count: read-only checks, display output, `echo`/`print` statements.

Present the count as a table:

```
Category              Count  Examples
──────────────────── ────── ────────────────────────────────────
Resource creation       N    gh repo create, snow sql setup.sql
Auth / secret ops       N    gh secret set, glab variable set
Verification            N    DESC USER, snow connection test
CI/CD operations        N    gh workflow run, glab pipeline run
──────────────────────────────────────────────────────────────
Total Ops               N
```

**Step 2 — Count Intent Expressions**

Count the number of distinct natural language goals the user has to express
to trigger the entire workflow (typically 1 for a single skill invocation).

**Step 3 — Calculate and Classify**

```
ICR = Total Ops / Intent Expressions = N
Classification: <relay | wrapper | partner | engine>
```

**Step 4 — Glass Box Assessment**

Evaluate the workflow on three Glass Box dimensions:

| Dimension | Present? | Notes |
|---|---|---|
| Observability | yes/no | Does it report what it created/changed? |
| Safe retry | yes/no | Can individual steps be retried without side effects? |
| Partial override | yes/no | Can the user skip or override specific steps? |

**Step 5 — Recommendations**

Identify the top 2–3 operations that could be compressed further:
- Which repeated patterns could become a single intent expression?
- Which verification steps could be folded into the preceding action?
- What Glass Box reporting is missing?

---

## Presenting Results

```
ICR Analysis: <workflow name>
─────────────────────────────────────
Total Ops          : N
Intent Expressions : N
ICR                : N  (<classification>)
─────────────────────────────────────
Glass Box score    : X/3  (observability + retry + override)
─────────────────────────────────────
Top compression opportunities:
  1. <opportunity>
  2. <opportunity>
```

Then ask:
```
ask_user_question:
  header: "Next step"
  question: "What would you like to do?"
  options:
    - label: "Apply IDD to improve this workflow"
    - label: "Rewrite a specific prompt in this workflow"
      description: "Hand off to rewrite-prompt"
    - label: "Done"
```
