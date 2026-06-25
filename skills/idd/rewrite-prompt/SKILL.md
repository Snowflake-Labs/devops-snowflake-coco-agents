---
name: idd-rewrite-prompt
description: >
  Guided rewrite of a prompt using the IDD Goal/Requirements/Constraints/Output
  structure. Collects each section interactively, generates the rewritten prompt,
  and optionally writes it to a file.
  Use when: "rewrite this prompt", "improve my prompt", "apply IDD to this",
  "IDD-ify this prompt".
---

## Stopping Points

Ask for the original prompt (to use as a starting point):

```
ask_user_question:
  header: "Original prompt"
  question: "Paste your existing prompt, or type 'new' to start from scratch."
  type: text
  defaultValue: ""
```

If an existing prompt is provided, read it and extract any existing Goal/Requirements/
Constraints/Output elements. These become the default values for the next four questions.

---

## Collect the Four IDD Sections

Ask each section separately with `ask_user_question`:

**Section 1 — Goal:**
```
ask_user_question:
  header: "Goal"
  question: "What is the desired state or outcome? What should be true after this prompt executes?"
  type: text
  defaultValue: "<extracted from original, or empty>"
```

**Section 2 — Requirements:**
```
ask_user_question:
  header: "Requirements"
  question: "What are the intent statements — what should happen, in outcome terms (not steps)? List one per line."
  type: text
  defaultValue: "<extracted from original>"
```

**Section 3 — Constraints:**
```
ask_user_question:
  header: "Constraints"
  question: "What are the scope limits, safety rules, and what-not-to-do? List one per line."
  type: text
  defaultValue: "<extracted from original>"
```

**Section 4 — Output:**
```
ask_user_question:
  header: "Output"
  question: "What does success look like? Include format, stdout summary, and any Glass Box signals."
  type: text
  defaultValue: "<extracted from original>"
```

---

## Generate and Present

Synthesise the four sections into a well-formatted IDD prompt:

```
[Goal]
<goal>

[Requirements]
<bullet list of requirements>

[Constraints]
<bullet list of constraints>

[Output]
<output specification>
```

Show the result and the IDD score delta (before vs. after if an original was provided).

Then ask:

```
ask_user_question:
  header: "Result"
  question: "What would you like to do with the rewritten prompt?"
  options:
    - label: "Write to a file"
      description: "Save to a path you specify"
    - label: "Copy to clipboard"
    - label: "Evaluate it"
      description: "Run the evaluate-prompt skill on the result"
    - label: "Done"
```

If "Write to a file":
```
ask_user_question:
  header: "File path"
  question: "Where should I save the prompt?"
  type: text
  defaultValue: ".cortex/prompts/my-prompt.md"
```
Then write the file.
