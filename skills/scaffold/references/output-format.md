# Output Formatting Rules

Loaded by scaffold sub-skills alongside `run-mode.md`.
All user-facing output MUST be rendered as formatted markdown.
Never output plain paragraphs for structured information.

---

## Why this matters (Guided mode only)

Use a blockquote with a bold header:

```
> **Why this matters**
> Body text — one to three sentences explaining the concept.
```

---

## What we'll do (inside plan mode)

Lead with a bold one-sentence summary, then use a table for resource lists or a
fenced block for command previews:

```
**What we'll do**

| Object    | Value                          |
|-----------|--------------------------------|
| Role      | ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_ROLE |
| Warehouse | ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_WH   |
```

Or for command previews:

```
**What we'll do**
\`\`\`
Creates: $REPO_PATH  (private, from template)
Clones:  ./$REPO_NAME
\`\`\`
```

---

## What we did (after execution)

Use a heading followed by a bullet list:

```
### What we did
- Role created: ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_ROLE
- Warehouse created: ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_WH
- User created and verified: ${PREFIX}_GH_${REPO_NAME_NORM}_COCO_AGENT_USER
```

---

## Gate check failure

```
> ⚠️ **Gate check failed:** [what is missing or wrong]
> Complete "[Step name]" before continuing.
```

---

## Warning (destructive / billable)

```
> ⚠️ **Warning:** This action is irreversible. Snowflake objects and the
> repository will be permanently deleted.
```

---

## Success

```
> ✓ **Done:** [brief summary of what was created or confirmed]
```

---

## Informational note

```
> ℹ️ **Note:** [additional context or next action]
```

---

## Petname rotation (generated name already taken)

```
> ℹ️ **Note:** `<login>/<taken-name>` is already taken — here's a fresh suggestion.
```

Then re-ask the name question with the new `defaultValue`.
After 3 failed rotations, fall back to a plain prompt with `defaultValue: "<login>/my-coco-agent"`.
