---
name: idd/evaluate-prompt
description: >
  Audit an existing prompt for IDD alignment. Scores it across four dimensions
  (Goal, Requirements, Constraints, Output), identifies gaps, and offers to
  hand off to the rewrite skill.
  Use when: "evaluate this prompt", "audit my prompt", "is this IDD", "score my prompt".
---

## Stopping Points

Ask the user to provide the prompt to evaluate:

```
ask_user_question:
  header: "Prompt"
  question: "Paste the prompt you want to evaluate, or provide a file path."
  type: text
  defaultValue: ""
```

If a file path is given, read the file. If pasted directly, use as-is.

Optionally ask for context:

```
ask_user_question:
  header: "Context"
  question: "What does this prompt do? (helps calibrate the evaluation)"
  type: text
  defaultValue: "A cortex exec / CI/CD automation prompt"
```

---

## Evaluation

Score each of the four IDD dimensions from 0–3:

| Score | Meaning |
|---|---|
| 0 | Absent — not present at all |
| 1 | Implicit — hinted at but not stated |
| 2 | Partial — present but incomplete or vague |
| 3 | Full — explicit, specific, and sufficient |

### Dimension 1 — Goal (Desired State)

Does the prompt declare **what should exist or be true** after execution?
- 0: No goal — only "do X" instructions
- 1: Role framing ("You are a reviewer") without desired state
- 2: Vague goal ("find bugs and report them")
- 3: Specific desired state with quality criterion ("surface issues precise enough that a fix agent can act without follow-up")

### Dimension 2 — Requirements (Intent Statements)

Are the requirements **outcome-focused** (what should happen) vs step-by-step (how to do it)?
- 0: No requirements
- 1: Pure procedure ("scan files, create issue, exit")
- 2: Mix of intent and procedure
- 3: Pure intent statements ("one issue per root cause", "body must include file/line/why/expected")

### Dimension 3 — Constraints

Does the prompt specify **scope limits, safety rules, and what not to do**?
- 0: No constraints
- 1: Single vague constraint ("don't add comments")
- 2: Partial constraints (scope defined but safety missing)
- 3: Full constraints (scope + safety + error handling + negative examples)

### Dimension 4 — Output (Glass Box)

Does the prompt specify **what success looks like** including observable evidence?
- 0: No output specification
- 1: Implicit ("create issues") — no format, no summary
- 2: Partial format ("use this title template") but no summary/Glass Box reporting
- 3: Full Glass Box — format + stdout summary + success/failure signals

---

## Presenting Results

Show the scores as a table:

```
Dimension      Score  Notes
──────────────────────────────────────────────────────
Goal            X/3   <what's there / what's missing>
Requirements    X/3   <what's there / what's missing>
Constraints     X/3   <what's there / what's missing>
Output          X/3   <what's there / what's missing>
──────────────────────────────────────────────────────
IDD Score      XX/12  <overall assessment>
ICR estimate   ~X     <rough ops-per-intent if inferable>
```

Classification:
- 0–4:  Syntaxist prompt — command relay, low agentic readiness
- 5–8:  Transitional — some intent, significant gaps
- 9–12: IDD-compliant — high ICR potential, strong agentic readiness

Then ask:

```
ask_user_question:
  header: "Next step"
  question: "What would you like to do?"
  options:
    - label: "Rewrite it using IDD"
      description: "Hand off to the rewrite-prompt skill"
    - label: "Just show me what to fix"
      description: "List the specific gaps with examples"
    - label: "Done"
```
