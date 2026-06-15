# Prompt Workflows

The `/idd` skill commands help you write better prompts and measure their effectiveness.
This page shows practical workflows for using them with your own project's CI/CD and
agent tasks.

## Adding a new IDD prompt for your project

Use `/idd-rewrite-prompt` to structure any existing prompt using the four IDD blocks:

```text
/idd-rewrite-prompt
```

The skill guides you through:

1. **Goal** — state the desired end state, not the steps to get there
2. **Requirements** — intent statements: what must be true, not how to achieve it
3. **Constraints** — scope, safety rules, what the agent must NOT do
4. **Output** — what success looks like (Glass Box reporting)

### Example: scan prompt before and after IDD

=== "Before"

    ```text
    Find SQL injection bugs and open GitHub issues.
    ```

    This gives the agent no scope, no safety constraints, and no way to know it is done.

=== "After IDD rewrite"

    ```text
    [Goal]
    Surface SQL injection vulnerabilities as GitHub issues that the fix agent
    can resolve without follow-up questions.

    [Requirements]
    - Read .agentignore before scanning
    - Identify SQL injection, hardcoded credentials, and insecure auth patterns
    - Issue body must include file path, line number, problematic snippet, and expected fix

    [Constraints]
    - One issue per distinct location (same bug in two functions = two issues)
    - Do not raise issues for style or minor readability concerns
    - Apply coco:auto-fix or coco:needs-review label based on COCO_MAX_AUTO ceiling

    [Output]
    gh issue create --title "[coco-agent] Bug: ..." --label coco:auto-fix ...
    "Scan complete. Found N issue(s). Ceiling: $COCO_MAX_AUTO"
    ```

## Refining an existing prompt

If your scan or fix prompt is producing noisy results (too many false positives,
fixes that miss the point), use `/idd-evaluate-prompt` to score it:

```text
/idd-evaluate-prompt
```

The skill scores your prompt on five IDD dimensions:

| Dimension | What it checks |
|-----------|---------------|
| Goal clarity | Is the desired end state explicit? |
| Requirement completeness | Are all intent statements present? |
| Constraint coverage | Are scope and safety rules defined? |
| Output measurability | Can success be verified? |
| ICR potential | Does the structure compress well to agent operations? |

## Measuring the ICR of a CI workflow

After your agent has run a full scaffold or scan→fix cycle:

```text
/idd-measure-icr
```

The skill counts the total operations performed and the human instructions that triggered
them. Use the output to track your team's agentic maturity over time.

**Example result:**

```text
Human instructions: 1  (/scaffold)
Agent operations:  48
ICR: 48 — Level 4 (Intent engine)
```

## Practical tips

- **Start conservative** — write the [Constraints] block first. Agents tend to overreach;
  constraints prevent that before it costs you a bad PR.

- **Glass Box Output** — always define what the final stdout should say. Vague output
  makes it impossible to automate verification.

- **Iterate with /idd-evaluate-prompt** — run the eval before committing a new prompt
  to your template. A score below 3/5 on any dimension predicts unreliable agent behaviour.

- **Custom scan prompts per project** — copy `.cortex/prompts/scan.md` from the template
  into your repo and adapt the [Constraints] for your language (the template scans Python;
  you can extend it to TypeScript, Go, etc.) without changing the [Goal] or [Output] blocks.
