---
name: idd
description: >
  Apply Intent-Driven Development (IDD) principles from Kamesh Sampath's IDD
  series to prompts, workflows, and CI/CD automation. Evaluate existing prompts
  for IDD alignment, rewrite them using the Goal/Requirements/Constraints/Output
  structure, or measure the Intent Compression Ratio (ICR) of a workflow.
  Use when: "review my prompt", "is this IDD-compliant", "rewrite this prompt",
  "measure ICR", "what is my ICR", "IDD audit", "intent compression ratio",
  "apply IDD", "improve my cortex exec prompt", "IDD principles".
---

## When to Load

Load when the user wants to evaluate, improve, or measure a prompt or workflow
through the IDD lens. Routes to the appropriate sub-skill based on intent.

## IDD Primer

IDD (Intent-Driven Development) treats prompts as design artifacts, not casual
inputs. Intent is the source of truth; code and execution are the outputs.

**IDD Prompt Template:**
```
[Goal]          — desired outcome / desired state
[Requirements]  — intent statements (not steps)
[Constraints]   — scope, safety rules, what not to do
[Output]        — what success looks like (Glass Box reporting)
```

**ICR (Intent Compression Ratio):** `Total Ops / Intent Expressions`
- ICR 1–3: command relay (the agent is just a wrapper)
- ICR 4–8: automation wrapper (meaningful compression)
- ICR 9+:  architectural partner (high agentic readiness)

**Target design point:** Glass Box Compression — high ICR + full observability
+ safe retry.

Reference: [Kamesh's IDD Blog Series](https://blogs.kameshs.dev)

## Routing Table

| Intent | Triggers | Load |
|---|---|---|
| Audit a prompt | "evaluate", "audit", "is this IDD", "review my prompt" | `idd/evaluate-prompt/SKILL.md` |
| Rewrite a prompt | "rewrite", "improve prompt", "apply IDD to", "fix my prompt" | `idd/rewrite-prompt/SKILL.md` |
| Measure ICR | "measure ICR", "what is ICR", "calculate ICR", "how much compression" | `idd/measure-icr/SKILL.md` |

If intent is ambiguous, ask:

```
ask_user_question:
  header: "IDD"
  question: "What would you like to do?"
  options:
    - label: "Evaluate a prompt"
      description: "Audit an existing prompt for IDD alignment and score it"
    - label: "Rewrite a prompt"
      description: "Guided rewrite using Goal/Requirements/Constraints/Output"
    - label: "Measure ICR"
      description: "Calculate the Intent Compression Ratio of a workflow"
```

## Shorthand Invocations

```
$devops-coco-agents:idd                   → ask intent, route to sub-skill
$devops-coco-agents:idd/evaluate-prompt   → load evaluate-prompt directly
$devops-coco-agents:idd/rewrite-prompt    → load rewrite-prompt directly
$devops-coco-agents:idd/measure-icr       → load measure-icr directly
```
